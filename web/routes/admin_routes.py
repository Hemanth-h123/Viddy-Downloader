from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from web.models import db, BlogPost, Feedback, PageVisit, User
from datetime import datetime
from slugify import slugify
from sqlalchemy import desc, func
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin access decorator
def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/')
@admin_required
def admin_dashboard():
    """Admin dashboard with overview statistics"""
    # Count total blog posts
    total_posts = BlogPost.query.count()
    published_posts = BlogPost.query.filter_by(published=True).count()
    
    # Count feedback by status
    feedback_stats = db.session.query(
        Feedback.status, func.count(Feedback.id)
    ).group_by(Feedback.status).all()
    
    # Get page visit statistics for the last 30 days
    visits_by_page = db.session.query(
        PageVisit.page, func.count(PageVisit.id)
    ).group_by(PageVisit.page).order_by(func.count(PageVisit.id).desc()).limit(10).all()
    
    return render_template('admin/dashboard.html', 
                          total_posts=total_posts,
                          published_posts=published_posts,
                          feedback_stats=dict(feedback_stats),
                          visits_by_page=visits_by_page)

# Blog post management
@admin_bp.route('/blog')
@admin_required
def blog_list():
    """List all blog posts for management"""
    posts = BlogPost.query.order_by(desc(BlogPost.created_at)).all()
    return render_template('admin/blog/list.html', posts=posts)

@admin_bp.route('/blog/new', methods=['GET', 'POST'])
@admin_required
def blog_new():
    """Create a new blog post"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        summary = request.form.get('summary')
        featured_image = request.form.get('featured_image')
        published = 'published' in request.form
        
        # Generate slug from title
        slug = slugify(title)
        
        # Check if slug already exists
        existing = BlogPost.query.filter_by(slug=slug).first()
        if existing:
            # Append a number to make the slug unique
            count = 1
            new_slug = f"{slug}-{count}"
            while BlogPost.query.filter_by(slug=new_slug).first():
                count += 1
                new_slug = f"{slug}-{count}"
            slug = new_slug
        
        post = BlogPost(
            title=title,
            slug=slug,
            content=content,
            summary=summary,
            featured_image=featured_image,
            published=published,
            author_id=current_user.id
        )
        
        db.session.add(post)
        db.session.commit()
        
        flash('Blog post created successfully!', 'success')
        return redirect(url_for('admin.blog_list'))
    
    return render_template('admin/blog/edit.html', post=None)

@admin_bp.route('/blog/edit/<int:post_id>', methods=['GET', 'POST'])
@admin_required
def blog_edit(post_id):
    """Edit an existing blog post"""
    post = BlogPost.query.get_or_404(post_id)
    
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        post.summary = request.form.get('summary')
        post.featured_image = request.form.get('featured_image')
        post.published = 'published' in request.form
        post.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Blog post updated successfully!', 'success')
        return redirect(url_for('admin.blog_list'))
    
    return render_template('admin/blog/edit.html', post=post)

@admin_bp.route('/blog/delete/<int:post_id>', methods=['POST'])
@admin_required
def blog_delete(post_id):
    """Delete a blog post"""
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    
    flash('Blog post deleted successfully!', 'success')
    return redirect(url_for('admin.blog_list'))

# Feedback management
@admin_bp.route('/feedback')
@admin_required
def feedback_list():
    """List all feedback for management"""
    status_filter = request.args.get('status', 'all')
    
    if status_filter != 'all':
        feedback = Feedback.query.filter_by(status=status_filter).order_by(desc(Feedback.created_at)).all()
    else:
        feedback = Feedback.query.order_by(desc(Feedback.created_at)).all()
    
    return render_template('admin/feedback/list.html', feedback=feedback, current_filter=status_filter)

@admin_bp.route('/feedback/<int:feedback_id>', methods=['GET', 'POST'])
@admin_required
def feedback_detail(feedback_id):
    """View and update feedback details"""
    feedback = Feedback.query.get_or_404(feedback_id)
    
    if request.method == 'POST':
        feedback.status = request.form.get('status')
        feedback.admin_notes = request.form.get('admin_notes')
        
        if feedback.status in ['resolved', 'closed'] and not feedback.resolved_at:
            feedback.resolved_at = datetime.utcnow()
        
        db.session.commit()
        flash('Feedback updated successfully!', 'success')
        return redirect(url_for('admin.feedback_list'))
    
    return render_template('admin/feedback/detail.html', feedback=feedback)

# Traffic analytics
@admin_bp.route('/traffic')
@admin_required
def traffic_analytics():
    """View traffic analytics"""
    # Get page visits by day for the last 30 days
    visits_by_day = db.session.query(
        func.date(PageVisit.timestamp).label('date'),
        func.count(PageVisit.id).label('count')
    ).group_by(func.date(PageVisit.timestamp)).order_by(func.date(PageVisit.timestamp)).all()
    
    # Get top pages
    top_pages = db.session.query(
        PageVisit.page,
        func.count(PageVisit.id).label('count')
    ).group_by(PageVisit.page).order_by(func.count(PageVisit.id).desc()).limit(10).all()
    
    # Format data for charts
    chart_data = {
        'dates': [str(visit.date) for visit in visits_by_day],
        'counts': [visit.count for visit in visits_by_day],
        'pages': [page.page for page in top_pages],
        'page_counts': [page.count for page in top_pages]
    }
    
    return render_template('admin/traffic.html', chart_data=json.dumps(chart_data))