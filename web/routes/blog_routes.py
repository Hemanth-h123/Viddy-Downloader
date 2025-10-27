from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for
from flask_login import current_user
from sqlalchemy import desc

from web.models import BlogPost, PageVisit, db

blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/blog')
def blog_index():
    """Display the blog index page with all published posts"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    try:
        # Record page visit for traffic tracking
        if request.remote_addr:
            visit = PageVisit(
                page='blog',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                referrer=request.referrer,
                user_id=current_user.id if not current_user.is_anonymous else None
            )
            db.session.add(visit)
            db.session.commit()
        
        # Get all published blog posts, newest first
        posts = BlogPost.query.filter_by(published=True).order_by(
            desc(BlogPost.created_at)
        ).paginate(page=page, per_page=per_page)
        
        return render_template('blog/index.html', posts=posts)
    except Exception as e:
        db.session.rollback()
        # Return a simple blog page with no posts if there's an error
        return render_template('blog/index.html', posts=None)

@blog_bp.route('/blog/<slug>')
def blog_post(slug):
    """Display a single blog post by its slug"""
    try:
        post = BlogPost.query.filter_by(slug=slug, published=True).first_or_404()
        
        # Record page visit and increment view count
        if request.remote_addr:
            visit = PageVisit(
                page=f'blog/{slug}',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                referrer=request.referrer,
                user_id=current_user.id if not current_user.is_anonymous else None
            )
            db.session.add(visit)
            
            # Increment view count
            post.views += 1
            db.session.commit()
        
        return render_template('blog/post.html', post=post)
    except Exception as e:
        db.session.rollback()
        # Log the error
        current_app.logger.error(f"Error displaying blog post {slug}: {str(e)}")
        # Redirect to blog index with a flash message
        flash("Sorry, we couldn't find that blog post or an error occurred.", "warning")
        return redirect(url_for('blog.blog_index'))