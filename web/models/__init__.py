from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta

# Initialize SQLAlchemy
db = SQLAlchemy()

class User(db.Model, UserMixin):
    """User model for authentication and profile information"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationships
    downloads = db.relationship('Download', backref='user', lazy=True)
    subscriptions = db.relationship('Subscription', backref='user', lazy=True)
    blog_posts = db.relationship('BlogPost', backref='author', lazy=True)
    feedbacks = db.relationship('Feedback', backref='user', lazy=True)
    oauth_accounts = db.relationship('OAuthAccount', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'
    
    @property
    def is_subscribed(self):
        """Check if user has an active subscription"""
        return self.subscription is not None and self.subscription.is_active()
    
    @property
    def subscription(self):
        """Get the user's active subscription if any"""
        return Subscription.query.filter_by(
            user_id=self.id, 
            status='active'
        ).first()
        
    def is_premium(self):
        """Check if user has an active premium subscription"""
        return self.is_subscribed

class OAuthAccount(db.Model):
    """Link external OAuth provider identity to a local user"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    provider = db.Column(db.String(50), nullable=False)  # 'google' or 'facebook'
    provider_user_id = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('provider', 'provider_user_id', name='uq_provider_identity'),
    )

class PasswordReset(db.Model):
    """Store one-time password reset codes"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    code = db.Column(db.String(10), nullable=False)  # numeric OTP code
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def create_for(user, code, ttl_minutes=10):
        entry = PasswordReset(
            user_id=user.id,
            code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes),
            used=False
        )
        db.session.add(entry)
        db.session.commit()
        return entry

class Download(db.Model):
    """Download record model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    quality = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='queued')  # queued, downloading, completed, failed
    progress = db.Column(db.Integer, default=0)  # 0-100
    file_path = db.Column(db.String(500), nullable=True)
    error_message = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    title = db.Column(db.String(500), nullable=True)  # Video title
    duration = db.Column(db.Integer, nullable=True)  # Video duration in seconds
    size = db.Column(db.BigInteger, nullable=True)  # File size in bytes
    content_type = db.Column(db.String(10), default='video')  # 'video' or 'image'
    video_quality = db.Column(db.String(20), default='auto')  # Actual quality of the video (e.g., '720p', '1080p')
    
    def __repr__(self):
        return f'<Download {self.id} - {self.platform} - {self.content_type}>'

class Subscription(db.Model):
    """User subscription model"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_id = db.Column(db.String(50), nullable=False)  # premium, premium_plus
    status = db.Column(db.String(20), nullable=False)  # active, cancelled, expired
    payment_id = db.Column(db.String(100), nullable=True)  # Payment processor reference
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Subscription {self.id} - {self.plan_id}>'
    
    def is_active(self):
        """Check if subscription is active"""
        if self.status != 'active':
            return False
        
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
            
        return True


class BlogPost(db.Model):
    """Blog post model for the blog feature"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(500), nullable=True)
    featured_image = db.Column(db.String(500), nullable=True)
    published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    views = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<BlogPost {self.title}>'


class Feedback(db.Model):
    """Feedback model for user suggestions, issues, and bugs"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Can be anonymous
    name = db.Column(db.String(100), nullable=True)  # For anonymous users
    email = db.Column(db.String(120), nullable=True)  # For anonymous users
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    feedback_type = db.Column(db.String(50), nullable=False)  # suggestion, issue, bug, other
    status = db.Column(db.String(50), default='new')  # new, in_progress, resolved, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Feedback {self.id} - {self.subject}>'


class PageVisit(db.Model):
    """Page visit model for tracking site traffic"""
    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.String(200), nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    referrer = db.Column(db.String(500), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # If user is logged in
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PageVisit {self.page} at {self.timestamp}>'