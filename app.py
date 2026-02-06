#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ALL-in-one Downloader Web - A multi-platform video downloader with monetization features
"""

import json
import threading
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_file
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect, generate_csrf
from dotenv import load_dotenv
import os
import json
from datetime import datetime
import threading
from authlib.integrations.flask_client import OAuth
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import random
from sqlalchemy import func
from web.models import db, User, Download, Subscription
from web.downloaders import get_downloader, identify_platform
from web.monetization import MonetizationManager
from web.forms import LoginForm, RegisterForm, DownloadForm, SettingsForm
from web.utils import setup_logger, load_config, create_default_config

def create_app():
    # Initialize Flask app
    # Load environment variables from .env if present
    load_dotenv()
    app = Flask(__name__, 
                template_folder="web/templates",
                static_folder="web/static",
                static_url_path="/static")
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///downloader.db')
    # Use writable temp storage for SQLite on Render
    if os.environ.get('RENDER', '').lower() == 'true':
        uri = app.config['SQLALCHEMY_DATABASE_URI'] or ''
        if uri.startswith('sqlite:///'):
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/downloader.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # reCAPTCHA keys (human verification)
    app.config['RECAPTCHA_PUBLIC_KEY'] = os.environ.get('RECAPTCHA_PUBLIC_KEY')
    app.config['RECAPTCHA_PRIVATE_KEY'] = os.environ.get('RECAPTCHA_PRIVATE_KEY')
    # Mail settings for email verification and OTP
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_USERNAME'))
    # OAuth client IDs / secrets
    app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
    app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')
    app.config['FACEBOOK_CLIENT_ID'] = os.environ.get('FACEBOOK_CLIENT_ID')
    app.config['FACEBOOK_CLIENT_SECRET'] = os.environ.get('FACEBOOK_CLIENT_SECRET')
    # Feature flags
    app.config['SUSPEND_YOUTUBE'] = os.environ.get('SUSPEND_YOUTUBE', '').lower() == 'true'
    app.config['MONETIZATION_ENABLED'] = os.environ.get('MONETIZATION_ENABLED', 'true').lower() == 'true'
    app.config['ADSENSE_CLIENT_ID'] = os.environ.get('ADSENSE_CLIENT_ID', '')
    
    # Initialize database
    from web.models import db
    db.init_app(app)
    # Ensure database tables exist on startup (works with WSGI servers like gunicorn)
    try:
        with app.app_context():
            db.create_all()
    except Exception as e:
        app.logger = app.logger if hasattr(app, 'logger') else None
        if app.logger:
            app.logger.error(f"Database initialization failed: {e}")
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        from web.models import User, db
        return db.session.get(User, int(user_id))
    
    # Initialize Mail and OAuth
    mail = Mail(app)
    oauth = OAuth(app)
    # Register Google OAuth (OpenID Connect)
    if app.config['GOOGLE_CLIENT_ID'] and app.config['GOOGLE_CLIENT_SECRET']:
        oauth.register(
            name='google',
            client_id=app.config['GOOGLE_CLIENT_ID'],
            client_secret=app.config['GOOGLE_CLIENT_SECRET'],
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'}
        )
    # Register Facebook OAuth
    if app.config['FACEBOOK_CLIENT_ID'] and app.config['FACEBOOK_CLIENT_SECRET']:
        oauth.register(
            name='facebook',
            client_id=app.config['FACEBOOK_CLIENT_ID'],
            client_secret=app.config['FACEBOOK_CLIENT_SECRET'],
            api_base_url='https://graph.facebook.com/',
            access_token_url='https://graph.facebook.com/oauth/access_token',
            authorize_url='https://www.facebook.com/dialog/oauth',
            client_kwargs={'scope': 'email'}
        )
    # Token serializer for email verification
    app.config['TOKEN_SERIALIZER'] = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    # Attach to app for usage in routes
    app.mail = mail
    app.oauth = oauth
    # Register blueprints and routes
    
    return app

# Create app instance
app = create_app()

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Inject CSRF token into all templates
@app.context_processor
def inject_csrf_token():
    return {'csrf_token': generate_csrf()}

# Inject current year into all templates
from datetime import datetime
@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

# Inject app config into templates (for reCAPTCHA checks)
@app.context_processor
def inject_app_config():
    return {'app_config': app.config}

# Setup logging
logger = setup_logger()

# Ensure config exists
if not os.path.exists('config.json'):
    logger.info("Creating default configuration")
    create_default_config()

# Load configuration
config = load_config()

# Initialize monetization manager
monetization_manager = MonetizationManager(config)

def register_blueprints(app):
    # Import and register blueprints
    from web.routes.blog_routes import blog_bp
    from web.routes.feedback_routes import feedback_bp
    from web.routes.admin_routes import admin_bp
    
    app.register_blueprint(blog_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(admin_bp)

register_blueprints(app)

@app.route('/')
def index():
    """Home page"""
    form = DownloadForm()
    
    # Get download limits and usage for authenticated users
    downloads_today = 0
    daily_limit = 5  # Default
    max_file_size_mb = 500  # Default
    plan_id = 'free'  # Default
    images_today = 0
    images_limit = 'Unlimited'
    images_left = None
    
    if current_user.is_authenticated:
        # Determine user's plan using monetization manager
        plans = monetization_manager.get_subscription_plans()
        sub = current_user.subscription
        if sub and sub.is_active():
            plan = plans.get(sub.plan_id)
            plan_id = sub.plan_id
        else:
            plan = plans.get('free')
            plan_id = 'free'
        # Fallback if plan missing
        if plan is None:
            plan = {'limits': {'daily_downloads': 5, 'max_file_size_mb': 500}}
        
        daily_limit = plan.get('limits', {}).get('daily_downloads', 5)
        max_file_size_mb = plan.get('limits', {}).get('max_file_size_mb', 500)
        
        # Count today's video downloads
        today = datetime.now().date()
        downloads_today = Download.query.filter(
            Download.user_id == current_user.id,
            func.date(Download.created_at) == today,
            Download.content_type == 'video'
        ).count()

        # Count today's image downloads and compute remaining if free plan
        if plan_id == 'free':
            images_limit = 10
            images_today = Download.query.filter(
                Download.user_id == current_user.id,
                func.date(Download.created_at) == today,
                Download.content_type == 'image'
            ).count()
            try:
                images_left = max(0, int(images_limit) - int(images_today))
            except Exception:
                images_left = None
        else:
            images_limit = 'Unlimited'
            images_left = None
    
    return render_template('index.html', form=form, user=current_user, 
                          downloads_today=downloads_today, 
                          daily_limit=daily_limit,
                          max_file_size_mb=max_file_size_mb,
                          plan=plan_id,
                          images_today=images_today,
                          images_limit=images_limit,
                          images_left=images_left)

@app.route('/download', methods=['POST'])
@login_required
def download():
    """Handle video download request"""
    form = DownloadForm()
    if form.validate_on_submit():
        url = form.url.data
        quality = form.quality.data
        
        # Identify platform
        platform = identify_platform(url)
        if not platform:
            flash('Unsupported URL or platform', 'error')
            return redirect(url_for('index'))
        # Suspend specific platforms via env flags (e.g., YouTube)
        if platform.lower() == 'youtube' and os.environ.get('SUSPEND_YOUTUBE', '').lower() == 'true':
            flash('YouTube downloads are temporarily suspended. Please try again later.', 'error')
            return redirect(url_for('index'))
        
        # Determine content type (image or video)
        content_type = 'image' if any(x in url.lower() for x in ['pinterest', 'instagram', '/p/', '/photo/']) else 'video'
        
        # Check if user can download (based on subscription and content type)
        if not monetization_manager.can_download(current_user, content_type):
            if content_type == 'image':
                flash('You have reached your daily image download limit. Please upgrade to Premium.', 'error')
            else:
                flash('You have reached your download limit. Please upgrade to Premium.', 'error')
            return redirect(url_for('premium'))
        
        # Enforce quality limit for free users
        plans = monetization_manager.get_subscription_plans()
        sub = current_user.subscription
        if sub and sub.is_active():
            plan = plans.get(sub.plan_id)
        else:
            plan = plans.get('free')
            
        # For free users, enforce video quality limit
        if plan and plan.get('id') == 'free' and content_type == 'video':
            max_quality = plan.get('limits', {}).get('max_video_quality', '720p')
            # If requested quality is higher than allowed, downgrade it
            if quality in ['1080p', '2160p', '4K', 'Best'] and max_quality == '720p':
                quality = '720p'
                flash('Free users are limited to 720p video quality. Your download will proceed at 720p.', 'info')
        
        # Create download record with 'downloading' status
        download = Download(
            user_id=current_user.id,
            url=url,
            platform=platform,
            quality=quality,
            status='downloading',
            started_at=datetime.utcnow(),
            content_type=content_type,
            video_quality=quality if content_type == 'video' else None
        )
        db.session.add(download)
        db.session.commit()
        
        try:
            # Kick off download in background so UI can poll progress
            def run_download_task(download_id):
                with app.app_context():
                    dl = Download.query.get(download_id)
                    if not dl:
                        return
                    try:
                        downloader = get_downloader(dl.platform)
                        # Check if running on Render
                        is_render = os.environ.get('RENDER', '').lower() == 'true'
                        
                        if is_render:
                            # Use /tmp directory on Render which is writable
                            download_dir = os.path.join('/tmp', 'downloads')
                        else:
                            # Use local directory for development
                            download_dir = os.path.join(app.root_path, 'downloads')
                            
                        os.makedirs(download_dir, exist_ok=True)
                        # Ensure the directory is writable
                        os.chmod(download_dir, 0o755)
                        
                        extra_opts = None
                        if dl.platform.lower() == 'youtube':
                            extra_opts = {
                                "extractor_args": {
                                    "youtube": {
                                        "skip_webpage": False,
                                        "player_skip": False,
                                    }
                                },
                                "retries": 15,
                                "fragment_retries": 15,
                                "extractor_retries": 10,
                            }

                        def progress_cb(pct):
                            # Ensure progress updates are committed immediately
                            with app.app_context():
                                try:
                                    # Get fresh instance to avoid session conflicts
                                    current_dl = Download.query.get(download_id)
                                    if current_dl:
                                        current_dl.progress = int(pct)
                                        current_dl.status = 'downloading'
                                        db.session.commit()
                                except Exception as e:
                                    app.logger.error(f"Progress update error: {e}")

                        def status_cb(msg):
                            # Log status messages for debugging
                            app.logger.info(f"Download {download_id} status: {msg}")
                            pass

                        # Set a timeout for the download to prevent hanging
                        max_retries = 3
                        retry_count = 0
                        
                        while retry_count < max_retries:
                            try:
                                final_path = downloader.download(
                            url=dl.url,
                            save_path=download_dir,
                            quality=dl.quality,
                            progress_callback=progress_cb,
                            status_callback=status_cb,
                            extra_opts=extra_opts
                        )
                                
                                # If download succeeded, break the retry loop
                                if final_path and os.path.exists(final_path):
                                    break
                                    
                                retry_count += 1
                                app.logger.warning(f"Download attempt {retry_count} failed, retrying...")
                            except Exception as e:
                                retry_count += 1
                                app.logger.error(f"Download error (attempt {retry_count}): {e}")
                                if retry_count >= max_retries:
                                    raise
                                
                        if final_path and os.path.exists(final_path):
                            dl.status = 'completed'
                            dl.file_path = final_path
                            dl.completed_at = datetime.utcnow()
                            dl.progress = 100
                            try:
                                dl.size = os.path.getsize(final_path)
                            except Exception:
                                dl.size = None
                        else:
                            dl.status = 'failed'
                            dl.error_message = "Download failed after multiple attempts"
                        db.session.commit()
                    except Exception as e:
                        dl.status = 'failed'
                        dl.error_message = str(e)
                        db.session.commit()

            worker = threading.Thread(target=run_download_task, args=(download.id,), daemon=True)
            worker.start()
            flash('Download started. You can monitor progress on this page.', 'info')
        except Exception as e:
            download.status = 'failed'
            download.error_message = str(e)
            app.logger.error(f"Download failed: {e}")
        finally:
            db.session.commit()

        return redirect(url_for('downloads'))
    
    return redirect(url_for('index'))

@app.route('/downloads')
@login_required
def downloads():
    """Show user's downloads with pagination and daily limits"""
    from sqlalchemy import func
    page = 1
    try:
        page = int(request.args.get('page', 1))
        if page < 1:
            page = 1
    except Exception:
        page = 1
    per_page = 10
    base_q = Download.query.filter_by(user_id=current_user.id).order_by(Download.created_at.desc())
    total = base_q.count()
    user_downloads = base_q.limit(per_page).offset((page - 1) * per_page).all()
    has_prev = page > 1
    has_next = (page * per_page) < total

    # Compute daily limits and usage
    from datetime import timedelta
    since = datetime.utcnow() - timedelta(days=1)
    daily_count = Download.query.filter(Download.user_id == current_user.id, Download.created_at >= since).count()

    # Determine current plan and limits
    plans = monetization_manager.get_subscription_plans()
    sub = current_user.subscription
    if sub and sub.is_active():
        plan = plans.get(sub.plan_id)
        plan_id = sub.plan_id
    else:
        plan = plans.get('free')
        plan_id = 'free'
    
    # Handle case where plan might be None
    if plan is None:
        plan = {'limits': {'daily_downloads': 3}}
        plan_id = 'free'

    daily_limit_videos = plan.get('limits', {}).get('daily_downloads', 3)
    if isinstance(daily_limit_videos, str) and daily_limit_videos.lower() == 'unlimited':
        videos_remaining = None
    else:
        try:
            limit_val = int(daily_limit_videos)
        except Exception:
            limit_val = 3
        videos_remaining = max(limit_val - daily_count, 0)

    # Data usage and remaining for Free plan
    data_used = db.session.query(func.coalesce(func.sum(Download.size), 0)).filter(
        Download.user_id == current_user.id,
        Download.created_at >= since,
        Download.status == 'completed'
    ).scalar() or 0
    free_data_cap = 3 * 1024 * 1024 * 1024  # 3GB in bytes
    data_remaining_bytes = max(free_data_cap - data_used, 0) if plan_id == 'free' else None

    return render_template('downloads.html', downloads=user_downloads, page=page, has_prev=has_prev, has_next=has_next, total=total, per_page=per_page, daily_count=daily_count, data_used=data_used, free_data_cap=free_data_cap, daily_limit_videos=daily_limit_videos, videos_remaining=videos_remaining, data_remaining_bytes=data_remaining_bytes, plan_id=plan_id)

@app.route('/api/downloads/<int:download_id>/status')
@login_required
def api_download_status(download_id):
    # Force a fresh query to get latest progress
    db.session.expire_all()
    dl = Download.query.get_or_404(download_id)
    if dl.user_id != current_user.id:
        return jsonify({"error": "forbidden"}), 403
    return jsonify({
        "id": dl.id,
        "status": dl.status,
        "progress": dl.progress or 0,
        "file_path": bool(dl.file_path),
        "error_message": dl.error_message or ""
    })

@app.route('/serve/file/<int:download_id>')
@login_required
def serve_download_file(download_id):
    """Serve the downloaded file to the user"""
    dl = Download.query.get_or_404(download_id)
    if dl.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('downloads'))
    
    if dl.status != 'completed' or not dl.file_path or not os.path.exists(dl.file_path):
        flash('File not available for download', 'error')
        return redirect(url_for('downloads'))
    
    # Get filename from the path
    filename = os.path.basename(dl.file_path)
    
    # Determine content type based on file extension
    content_type = None
    if filename.lower().endswith(('.mp4', '.mov', '.avi')):
        content_type = 'video/mp4'
    elif filename.lower().endswith(('.jpg', '.jpeg')):
        content_type = 'image/jpeg'
    elif filename.lower().endswith('.png'):
        content_type = 'image/png'
    
    # Send the file as attachment
    return send_file(
        dl.file_path,
        as_attachment=True,
        download_name=filename,
        mimetype=content_type
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('Invalid email or password', 'error')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if email already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered', 'error')
            return render_template('register.html', form=form)
        
        # Create new user
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(
            email=form.email.data,
            username=form.username.data,
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()

        # Send verification email
        try:
            serializer = app.config.get('TOKEN_SERIALIZER')
            if serializer and hasattr(app, 'mail') and app.mail:
                token = serializer.dumps(new_user.email)
                verify_url = url_for('verify_email', token=token, _external=True)
                send_email(new_user.email, 'Verify your email', f'Click this link to verify your account: {verify_url}')
                flash('Registration successful! Check your email to verify your account.', 'success')
            else:
                flash('Registration successful! Email verification not configured.', 'info')
        except Exception as e:
            app.logger.error(f'Failed to send verification email: {e}')
            flash('Registration successful, but failed to send verification email.', 'error')

        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/premium')
@login_required
def premium():
    """Premium subscription page"""
    plans = monetization_manager.get_subscription_plans()
    return render_template('premium.html', plans=plans)

@app.route('/subscribe/<plan_id>', methods=['POST'])
@login_required
def subscribe(plan_id):
    """Handle subscription request"""
    # In a real app, this would integrate with payment processors
    # For now, we'll just create a subscription record
    subscription = Subscription(
        user_id=current_user.id,
        plan_id=plan_id,
        status='active',
        expires_at=None  # Would be set based on plan duration
    )
    db.session.add(subscription)
    db.session.commit()
    
    flash('Subscription activated!', 'success')
    return redirect(url_for('index'))

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    """Initiate payment for a subscription plan"""
    plan_id = request.form.get('plan')
    payment_method = request.form.get('payment_method', 'stripe')
    plans = monetization_manager.get_subscription_plans()
    plan = plans.get(plan_id)
    if not plan:
        flash('Invalid plan selected.', 'error')
        return redirect(url_for('premium'))
    if plan.get('price', 0) == 0:
        # Free plan: no payment, activate immediately
        return redirect(url_for('subscribe', plan_id=plan_id))
    result = monetization_manager.create_payment(plan_id, current_user.id, payment_method)
    if result.get('error'):
        flash(result['error'], 'error')
        return redirect(url_for('premium'))
    checkout_url = result.get('checkout_url')
    payment_id = result.get('payment_id')
    if not checkout_url or not payment_id:
        flash('Unable to start checkout. Please try again.', 'error')
        return redirect(url_for('premium'))
    sep = '&' if '?' in checkout_url else '?'
    checkout_url = f"{checkout_url}{sep}payment_id={payment_id}&plan_id={plan_id}&method={payment_method}"
    return redirect(checkout_url)

@app.route('/mock-stripe-checkout')
@login_required
def mock_stripe_checkout():
    """Demo Stripe checkout page"""
    plan_name = request.args.get('plan')
    price = request.args.get('price')
    payment_id = request.args.get('payment_id')
    plan_id = request.args.get('plan_id')
    method = request.args.get('method', 'stripe')
    if not payment_id or not plan_id:
        flash('Checkout session missing details.', 'error')
        return redirect(url_for('premium'))
    return render_template('payments/mock_checkout.html',
                           gateway='Stripe',
                           plan_name=plan_name,
                           price=price,
                           payment_id=payment_id,
                           plan_id=plan_id,
                           method=method)

@app.route('/mock-paypal-checkout')
@login_required
def mock_paypal_checkout():
    """Demo PayPal checkout page"""
    plan_name = request.args.get('plan')
    price = request.args.get('price')
    payment_id = request.args.get('payment_id')
    plan_id = request.args.get('plan_id')
    method = request.args.get('method', 'paypal')
    if not payment_id or not plan_id:
        flash('Checkout session missing details.', 'error')
        return redirect(url_for('premium'))
    return render_template('payments/mock_checkout.html',
                           gateway='PayPal',
                           plan_name=plan_name,
                           price=price,
                           payment_id=payment_id,
                           plan_id=plan_id,
                           method=method)

@app.route('/payment/complete', methods=['POST'])
@login_required
def payment_complete():
    """Finalize payment and activate subscription"""
    payment_id = request.form.get('payment_id')
    plan_id = request.form.get('plan_id')
    method = request.form.get('method')
    plans = monetization_manager.get_subscription_plans()
    plan = plans.get(plan_id)
    if not plan or plan.get('price', 0) == 0:
        flash('Invalid paid plan.', 'error')
        return redirect(url_for('premium'))
    subscription = Subscription(
        user_id=current_user.id,
        plan_id=plan_id,
        status='active',
        payment_id=payment_id,
        expires_at=None
    )
    db.session.add(subscription)
    db.session.commit()
    flash('Payment completed! Subscription activated.', 'success')
    return redirect(url_for('premium'))

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User settings page"""
    form = SettingsForm()

    # Prefill form with current user's profile info
    if request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    # Determine current subscription/plan for display in settings
    subscription = current_user.subscription
    plans = monetization_manager.get_subscription_plans()
    current_plan_id = (subscription.plan_id if subscription and subscription.is_active() else 'free')
    current_plan = plans.get(current_plan_id, plans.get('free'))
    current_plan_name = current_plan.get('name')

    if form.validate_on_submit():
        # Update editable profile fields
        try:
            new_username = (form.username.data or '').strip()
            if new_username and new_username != current_user.username:
                current_user.username = new_username
                db.session.commit()
                flash('Profile updated successfully.', 'success')
            else:
                flash('Settings saved successfully.', 'success')
                
            # Handle cookie file upload
            if 'cookie_file' in request.files:
                cookie_file = request.files['cookie_file']
                if cookie_file.filename != '':
                    is_render = os.environ.get('RENDER', '').lower() == 'true'
                    cookie_path = '/tmp/cookies.txt' if is_render else os.path.join(app.root_path, 'cookies.txt')
                    try:
                        cookie_file.save(cookie_path)
                        flash('YouTube cookies file uploaded successfully!', 'success')
                    except Exception as e:
                        flash(f'Failed to save cookies file: {e}', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to update profile: {e}', 'error')
        return redirect(url_for('settings'))

    return render_template(
        'settings.html',
        form=form,
        current_plan=current_plan,
        current_plan_id=current_plan_id,
        current_plan_name=current_plan_name,
        subscription=subscription
    )

@app.route('/clear_history', methods=['POST'])
@login_required
def clear_history():
    """Clear all download history for the current user"""
    try:
        Download.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        flash('Download history cleared.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to clear history: {e}', 'error')
    return redirect(url_for('downloads'))

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    """Delete the current user's account and related data"""
    try:
        uid = current_user.id
        # Log the user out first
        logout_user()
        # Delete related records
        Download.query.filter_by(user_id=uid).delete()
        Subscription.query.filter_by(user_id=uid).delete()
        user = User.query.get(uid)
        if user:
            db.session.delete(user)
        db.session.commit()
        flash('Your account has been deleted.', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to delete account: {e}', 'error')
        return redirect(url_for('settings'))

@app.route('/download_file/<int:download_id>')
@login_required
def download_file(download_id):
    """Download a completed file"""
    download = Download.query.get_or_404(download_id)
    
    # Ensure the download belongs to the current user
    if download.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('downloads'))
    
    # Ensure the download is completed and has a file path
    if download.status != 'completed' or not download.file_path:
        flash('File not available for download', 'error')
        return redirect(url_for('downloads'))
    
    # Check if file exists
    if not os.path.exists(download.file_path):
        flash('File not found', 'error')
        return redirect(url_for('downloads'))
    
    # Return the file
    return send_file(download.file_path, as_attachment=True)

@app.route('/delete_download/<int:download_id>', methods=['POST'])
@login_required
def delete_download(download_id):
    """Delete a download"""
    download = Download.query.get_or_404(download_id)
    
    # Ensure the download belongs to the current user
    if download.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('downloads'))
    
    # Delete the file if it exists
    if download.file_path and os.path.exists(download.file_path):
        try:
            os.remove(download.file_path)
        except Exception as e:
            app.logger.error(f"Error deleting file: {e}")
    
    # Delete the download record
    db.session.delete(download)
    db.session.commit()
    
    flash('Download deleted', 'success')
    return redirect(url_for('downloads'))

@app.route('/cancel_download/<int:download_id>', methods=['POST'])
@login_required
def cancel_download(download_id):
    """Cancel a download in progress"""
    download = Download.query.get_or_404(download_id)
    
    # Ensure the download belongs to the current user
    if download.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('downloads'))
    
    # Ensure the download is in progress
    if download.status != 'downloading':
        flash('Download is not in progress', 'error')
        return redirect(url_for('downloads'))
    
    # Update the download status
    download.status = 'cancelled'
    db.session.commit()
    
    flash('Download cancelled', 'success')
    return redirect(url_for('downloads'))

@app.route('/retry_download/<int:download_id>', methods=['POST'])
@login_required
def retry_download(download_id):
    """Retry a failed download"""
    download = Download.query.get_or_404(download_id)
    
    # Ensure the download belongs to the current user
    if download.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('downloads'))
    
    # Ensure the download is failed
    if download.status != 'failed':
        flash('Only failed downloads can be retried', 'error')
        return redirect(url_for('downloads'))
    
    # Update the download status
    download.status = 'downloading'
    download.error_message = None
    download.started_at = datetime.utcnow()
    db.session.commit()
    
    try:
        # Get the appropriate downloader
        downloader = get_downloader(download.platform)
        
        # Create download directory if it doesn't exist
        download_dir = os.path.join(app.root_path, 'downloads')
        os.makedirs(download_dir, exist_ok=True)
        
        # Start the download immediately
        download_path = downloader.download(
            url=download.url,
            save_path=download_dir,
            quality=download.quality
        )
        
        # Update download status
        if download_path and os.path.exists(download_path):
            download.status = 'completed'
            download.file_path = download_path
            download.completed_at = datetime.utcnow()
            download.progress = 100
            try:
                download.size = os.path.getsize(download_path)
            except Exception:
                download.size = None
            flash('Download completed successfully!', 'success')
        else:
            download.status = 'failed'
            flash('Download failed. Please try again.', 'error')
    
    except Exception as e:
        download.status = 'failed'
        download.error_message = str(e)
        app.logger.error(f"Download failed: {e}")
        flash(f'Download failed: {str(e)}', 'error')
    
    finally:
        db.session.commit()
        
    return redirect(url_for('downloads'))

@app.route('/change_subscription', methods=['POST'])
@login_required
def change_subscription():
    """Allow users to upgrade or downgrade their subscription plan"""
    plan_id = request.form.get('plan')
    plans = monetization_manager.get_subscription_plans()
    plan = plans.get(plan_id)
    if not plan:
        flash('Invalid plan selected.', 'error')
        return redirect(url_for('premium'))

    # Get current subscription
    sub = Subscription.query.filter_by(user_id=current_user.id).first()
    if not sub or not sub.is_active():
        # No active subscription: follow normal flow
        if plan.get('price', 0) == 0:
            return redirect(url_for('subscribe', plan_id=plan_id))
        else:
            # Require checkout for initiating paid plans
            request_form = request.form.to_dict()
            request_form['plan'] = plan_id
            request_form.setdefault('payment_method', 'stripe')
            # Emulate a POST redirect to checkout by calling function directly
            return checkout()

    # Active subscription: change plan immediately
    try:
        sub.plan_id = plan_id
        sub.status = 'active'
        db.session.commit()
        flash(f'Plan changed to {plan.get("name")}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to change plan: {e}', 'error')
    return redirect(url_for('premium'))

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return render_template('500.html'), 500


@app.route('/auth/google')
def auth_google():
    if not hasattr(app, 'oauth') or 'google' not in app.oauth._clients:
        flash('Google login is not configured.', 'error')
        return redirect(url_for('login'))
    redirect_uri = url_for('auth_google_callback', _external=True)
    return app.oauth.google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def auth_google_callback():
    if 'google' not in app.oauth._clients:
        flash('Google login is not configured.', 'error')
        return redirect(url_for('login'))
    token = app.oauth.google.authorize_access_token()
    userinfo = token.get('userinfo') or {}
    email = userinfo.get('email')
    provider_user_id = userinfo.get('sub')
    name = userinfo.get('name') or (email.split('@')[0] if email else 'user')
    if not email or not provider_user_id:
        flash('Failed to retrieve Google user info.', 'error')
        return redirect(url_for('login'))
    from web.models import OAuthAccount
    account = OAuthAccount.query.filter_by(provider='google', provider_user_id=provider_user_id).first()
    if account:
        user = account.user
    else:
        # Link to existing user by email or create new
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, username=name, password=generate_password_hash(os.urandom(16)))
            db.session.add(user)
            db.session.commit()
        link = OAuthAccount(user_id=user.id, provider='google', provider_user_id=provider_user_id)
        db.session.add(link)
        db.session.commit()
    login_user(user)
    flash('Logged in with Google.', 'success')
    return redirect(url_for('index'))

@app.route('/auth/facebook')
def auth_facebook():
    if not hasattr(app, 'oauth') or 'facebook' not in app.oauth._clients:
        flash('Facebook login is not configured.', 'error')
        return redirect(url_for('login'))
    redirect_uri = url_for('auth_facebook_callback', _external=True)
    return app.oauth.facebook.authorize_redirect(redirect_uri)

@app.route('/auth/facebook/callback')
def auth_facebook_callback():
    if 'facebook' not in app.oauth._clients:
        flash('Facebook login is not configured.', 'error')
        return redirect(url_for('login'))
    token = app.oauth.facebook.authorize_access_token()
    resp = app.oauth.facebook.get('me?fields=id,name,email')
    data = resp.json()
    provider_user_id = data.get('id')
    email = data.get('email')
    name = data.get('name') or (email.split('@')[0] if email else 'user')
    if not provider_user_id:
        flash('Failed to retrieve Facebook user info.', 'error')
        return redirect(url_for('login'))
    from web.models import OAuthAccount
    account = OAuthAccount.query.filter_by(provider='facebook', provider_user_id=provider_user_id).first()
    if account:
        user = account.user
    else:
        user = None
        if email:
            user = User.query.filter_by(email=email).first()
        if not user:
            # Create a user even if email missing
            pseudo_email = email or f"fb_{provider_user_id}@example.com"
            user = User(email=pseudo_email, username=name, password=generate_password_hash(os.urandom(16)))
            db.session.add(user)
            db.session.commit()
        link = OAuthAccount(user_id=user.id, provider='facebook', provider_user_id=provider_user_id)
        db.session.add(link)
        db.session.commit()
    login_user(user)
    flash('Logged in with Facebook.', 'success')
    return redirect(url_for('index'))


def send_email(to, subject, body):
    try:
        msg = Message(subject=subject, recipients=[to], body=body)
        app.mail.send(msg)
        return True
    except Exception as e:
        app.logger.error(f"Email send failed: {e}")
        return False

@app.route('/verify-email')
def verify_email():
    token = request.args.get('token')
    if not token:
        flash('Missing verification token.', 'error')
        return redirect(url_for('login'))
    serializer = app.config['TOKEN_SERIALIZER']
    try:
        email = serializer.loads(token, max_age=3600)
    except SignatureExpired:
        flash('Verification link expired.', 'error')
        return redirect(url_for('login'))
    except BadSignature:
        flash('Invalid verification link.', 'error')
        return redirect(url_for('login'))
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Account not found.', 'error')
        return redirect(url_for('login'))
    # Mark verified via a simple flag in session (no schema change)
    session[f'verified:{user.id}'] = True
    flash('Email verified successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    from web.forms import PasswordResetRequestForm
    form = PasswordResetRequestForm()

    # Ensure mail is configured before attempting to send emails
    mail_cfg_ok = bool(app.mail) and bool(app.config.get('MAIL_USERNAME')) and bool(app.config.get('MAIL_PASSWORD'))
    if not mail_cfg_ok and request.method == 'POST':
        flash('Password reset email is not configured.', 'error')
        return render_template('forgot_password.html', form=form)

    # Simple rate limit: one request per minute per session
    try:
        last_iso = session.get('fp_last')
        if last_iso:
            last_dt = datetime.fromisoformat(last_iso)
            if (datetime.utcnow() - last_dt).total_seconds() < 60:
                flash('Please wait a minute before requesting another OTP.', 'warning')
                return render_template('forgot_password.html', form=form)
    except Exception:
        pass

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash('If the email exists, an OTP was sent.', 'info')
            return redirect(url_for('forgot_password'))
        # Block local reset for accounts linked via OAuth
        from web.models import OAuthAccount
        linked_oauth = OAuthAccount.query.filter_by(user_id=user.id).first()
        if linked_oauth:
            flash('This account uses social login (Google/Facebook). Reset your password via your provider.', 'warning')
            return render_template('forgot_password.html', form=form)
        code = f"{random.randint(100000, 999999)}"
        from web.models import PasswordReset
        PasswordReset.create_for(user, code, ttl_minutes=10)
        send_email(user.email, 'Your password reset OTP', f'Use this code to reset your password: {code}')
        # Record request time
        session['fp_last'] = datetime.utcnow().isoformat()
        flash('An OTP has been sent to your email.', 'success')
        return redirect(url_for('reset_password'))
    return render_template('forgot_password.html', form=form)

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    from web.forms import PasswordResetConfirmForm
    from web.models import PasswordReset
    form = PasswordResetConfirmForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash('Invalid email or OTP.', 'error')
            return render_template('reset_password.html', form=form)

        # Find latest unused code
        pr = PasswordReset.query.filter_by(user_id=user.id, used=False).order_by(PasswordReset.created_at.desc()).first()
        if not pr or pr.code != form.code.data or pr.expires_at < datetime.utcnow():
            flash('Invalid or expired OTP.', 'error')
            return render_template('reset_password.html', form=form)
        pr.used = True
        user.password = generate_password_hash(form.new_password.data)
        db.session.commit()
        flash('Password reset successful. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Use PORT environment variable for Render deployment
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
