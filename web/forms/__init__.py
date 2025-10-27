#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Forms for the web application
"""

from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, URL, ValidationError

# Make reCAPTCHA optional when keys are not configured
from flask import current_app

class OptionalRecaptchaField(RecaptchaField):
    def validate(self, form, extra_validators=tuple()):
        try:
            cfg = current_app.config
            pub = cfg.get('RECAPTCHA_PUBLIC_KEY')
            priv = cfg.get('RECAPTCHA_PRIVATE_KEY')
            if not pub or not priv:
                # Skip validation entirely if reCAPTCHA is not configured
                return True
        except Exception:
            # If app context is unavailable, fail open to avoid blocking auth
            return True
        return super().validate(form, extra_validators)

class LoginForm(FlaskForm):
    """User login form"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    recaptcha = OptionalRecaptchaField()
    submit = SubmitField('Log In')

class RegisterForm(FlaskForm):
    """User registration form"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    recaptcha = OptionalRecaptchaField()
    submit = SubmitField('Register')

class DownloadForm(FlaskForm):
    """Video download form"""
    url = StringField('Video URL', validators=[DataRequired(), URL()])
    quality = SelectField('Quality', choices=[
        ('Best', 'Best Quality'),
        ('1080p', '1080p'),
        ('720p', '720p'),
        ('480p', '480p'),
        ('360p', '360p'),
        ('Audio Only', 'Audio Only')
    ])
    submit = SubmitField('Download')

class SettingsForm(FlaskForm):
    """User settings form"""
    username = StringField('User Name', validators=[Length(min=3, max=50)])
    email = StringField('Email', validators=[Email()])
    save_path = StringField('Default Save Path')
    concurrent_downloads = SelectField('Concurrent Downloads', choices=[(str(i), str(i)) for i in range(1, 6)])
    theme = SelectField('Theme', choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('system', 'System Default')
    ])
    check_updates = BooleanField('Check for Updates Automatically')
    allow_analytics = BooleanField('Allow Anonymous Usage Analytics')
    ad_frequency = SelectField('Ad Frequency', choices=[
        ('none', 'None'),
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High')
    ])
    submit = SubmitField('Save Settings')

class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    recaptcha = OptionalRecaptchaField()
    submit = SubmitField('Send OTP')

class PasswordResetConfirmForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    code = StringField('OTP Code', validators=[DataRequired(), Length(min=4, max=10)])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Reset Password')

class PaymentForm(FlaskForm):
    """Payment form for premium subscriptions"""
    plan = SelectField('Subscription Plan', choices=[
        ('basic', 'Basic'),
        ('pro', 'Pro')
    ])
    payment_method = SelectField('Payment Method', choices=[
        ('stripe', 'Credit Card (Stripe)'),
        ('paypal', 'PayPal')
    ])
    submit = SubmitField('Proceed to Payment')