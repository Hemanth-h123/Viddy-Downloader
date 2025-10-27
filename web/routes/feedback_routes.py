from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from web.models import db, Feedback, PageVisit
from datetime import datetime

feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route('/feedback', methods=['GET', 'POST'])
def feedback():
    """Display and handle the feedback form"""
    # Record page visit for traffic tracking
    if request.remote_addr:
        visit = PageVisit(
            page='feedback',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            referrer=request.referrer,
            user_id=current_user.id if not current_user.is_anonymous else None
        )
        db.session.add(visit)
        db.session.commit()
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        feedback_type = request.form.get('feedback_type')
        
        # Create new feedback entry
        feedback = Feedback(
            user_id=current_user.id if not current_user.is_anonymous else None,
            name=name if current_user.is_anonymous else current_user.username,
            email=email if current_user.is_anonymous else current_user.email,
            subject=subject,
            message=message,
            feedback_type=feedback_type,
            status='new'
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        flash('Thank you for your feedback! We appreciate your input.', 'success')
        return redirect(url_for('feedback.thank_you'))
    
    return render_template('feedback/form.html')

@feedback_bp.route('/feedback/thank-you')
def thank_you():
    """Thank you page after submitting feedback"""
    return render_template('feedback/thank_you.html')