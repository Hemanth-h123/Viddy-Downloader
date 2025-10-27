#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Monetization module for the web application
"""

import os
import time
import json
import qrcode
from datetime import datetime, timedelta
import logging

# Import payment processors conditionally to avoid errors if not installed
try:
    import paypalrestsdk
    PAYPAL_AVAILABLE = True
except ImportError:
    PAYPAL_AVAILABLE = False

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

logger = logging.getLogger(__name__)

class MonetizationManager:
    """Manages monetization features including premium subscriptions, ads, and payments"""
    
    def __init__(self, config):
        """Initialize the monetization manager
        
        Args:
            config (dict): The application configuration
        """
        self.config = config
        # Updated plan definitions with limits and period/popular keys
        self.subscription_plans = {
            "free": {
                "name": "Free",
                "price": 0,
                "currency": "USD",
                "period": "month",
                "popular": False,
                "features": [
                    "Basic downloader",
                    "Standard support",
                    "Up to 5 videos/day",
                    "Up to 10 images/day",
                    "Video quality up to 720p",
                    "Max file size: 500MB"
                ],
                "limits": {
                    "daily_downloads": 5,
                    "daily_image_downloads": 10,
                    "max_file_size_mb": 500,
                    "max_video_quality": "720p",
                    "ad_free": False
                }
            },
            "basic": {
                "name": "Basic",
                "price": 4.99,
                "currency": "USD",
                "period": "month",
                "popular": True,
                "features": [
                    "Up to 30 videos/day",
                    "HD quality downloads",
                    "Priority support"
                ],
                "limits": {
                    "daily_downloads": 30,
                    "daily_image_downloads": "Unlimited",
                    "max_file_size_mb": 1000,
                    "ad_free": False
                }
            },
            "pro": {
                "name": "Pro",
                "price": 9.99,
                "currency": "USD",
                "period": "month",
                "popular": False,
                "features": [
                    "Unlimited downloads",
                    "Batch downloading",
                    "Scheduled downloads",
                    "Custom video quality presets",
                    "Cloud storage integration"
                ],
                "limits": {
                    "daily_downloads": "Unlimited",
                    "daily_image_downloads": "Unlimited",
                    "max_file_size_mb": 2000,
                    "ad_free": True
                }
            }
        }
        
        # Initialize payment processors if available
        if PAYPAL_AVAILABLE and 'paypal' in config.get('monetization', {}):
            paypal_config = config['monetization']['paypal']
            paypalrestsdk.configure({
                "mode": paypal_config.get('mode', 'sandbox'),
                "client_id": paypal_config.get('client_id', ''),
                "client_secret": paypal_config.get('client_secret', '')
            })
        
        if STRIPE_AVAILABLE and 'stripe' in config.get('monetization', {}):
            stripe_config = config['monetization']['stripe']
            stripe.api_key = stripe_config.get('api_key', '')
    
    def get_subscription_plans(self):
        """Get available subscription plans
        
        Returns:
            dict: Available subscription plans
        """
        return self.subscription_plans
    
    def is_premium(self, user):
        """Check if the user has an active premium subscription
        
        Args:
            user: The user object to check
            
        Returns:
            bool: True if the user has an active premium subscription, False otherwise
        """
        if not user or not user.is_authenticated:
            return False
            
        return user.is_premium()
    
    def can_download(self, user, content_type="video"):
        """Check if the user can download videos or images based on their subscription.
        Enforces per-plan daily download count, and 3GB/day data cap for Free.
        
        Args:
            user: The user attempting to download
            content_type: Either "video" or "image" to check appropriate limits
        """
        # For non-authenticated users, block
        if not user or not user.is_authenticated:
            return False
        
        # Determine plan and limits
        sub = user.subscription
        plans = self.get_subscription_plans()
        if sub and sub.is_active():
            # Map legacy plan IDs to current ones
            legacy_map = {"premium": "basic", "premium_plus": "pro"}
            effective_id = legacy_map.get(sub.plan_id, sub.plan_id)
            plan = plans.get(effective_id)
            plan_id = effective_id if plan else "free"
            if plan is None:
                logger.warning("Unknown plan_id '%s'; defaulting to free", sub.plan_id)
                plan = plans.get("free")
        else:
            plan = plans.get("free")
            plan_id = "free"
        
        # Get today's date (reset at midnight)
        from web.models import Download
        from datetime import datetime, timedelta, time
        from sqlalchemy import func
        
        # Use today's date from midnight (00:00:00) for daily reset
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Check appropriate limit based on content type
        if content_type == "image":
            daily_limit = plan.get("limits", {}).get("daily_image_downloads", 10)
            content_filter = {"content_type": "image"}
        else:  # Default to video
            daily_limit = plan.get("limits", {}).get("daily_downloads", 5)
            content_filter = {"content_type": "video"}
        
        if isinstance(daily_limit, str) and daily_limit.lower() == "unlimited":
            # Unlimited daily downloads; no count cap
            limit_val = None
        else:
            try:
                limit_val = int(daily_limit)
            except Exception:
                limit_val = 5 if content_type == "video" else 10
        
        # Count downloads since midnight today
        recent_count = Download.query.filter(
            Download.user_id == user.id,
            Download.created_at >= today,
            Download.content_type == content_type
        ).count()
        
        if limit_val is not None and recent_count >= limit_val:
            return False
        
        # Enforce data cap for Free plan: 3GB/day based on completed sizes
        if plan_id == "free":
            free_cap_bytes = 3 * 1024 * 1024 * 1024
            data_used = Download.query.with_entities(func.coalesce(func.sum(Download.size), 0)).filter(
                Download.user_id == user.id,
                Download.created_at >= today,
                Download.status == 'completed'
            ).scalar() or 0
            if data_used >= free_cap_bytes:
                return False
        
        return True
    
    def should_show_ad(self, user):
        """Determine if an ad should be shown based on user's subscription"""
        try:
            if user and user.is_authenticated:
                sub = user.subscription
                plans = self.get_subscription_plans()
                if sub and sub.is_active():
                    plan = plans.get(sub.plan_id)
                    if plan and plan.get("limits", {}).get("ad_free", False):
                        return False
        except Exception:
            pass
        
        # Fallback to configured ad frequency
        ad_frequency = self.config.get("ad_frequency", "normal")
        if ad_frequency == "none":
            return False
        elif ad_frequency == "low":
            return (hash(str(user.id) + str(int(time.time() / 3600))) % 5) == 0
        elif ad_frequency == "high":
            return (hash(str(user.id) + str(int(time.time() / 3600))) % 2) == 0
        else:
            return (hash(str(user.id) + str(int(time.time() / 3600))) % 3) == 0
    
    def create_payment(self, plan_id, user_id, payment_method="stripe"):
        """Create a payment for subscription
        
        Args:
            plan_id (str): The subscription plan ID
            user_id (int): The user ID
            payment_method (str): The payment method (stripe, paypal)
            
        Returns:
            dict: Payment information including URL for checkout
        """
        plan = self.subscription_plans.get(plan_id)
        if not plan:
            return {"error": "Invalid subscription plan"}
        
        if payment_method == "stripe" and STRIPE_AVAILABLE:
            return self._create_stripe_payment(plan, user_id)
        elif payment_method == "paypal" and PAYPAL_AVAILABLE:
            return self._create_paypal_payment(plan, user_id)
        else:
            return {"error": "Payment method not available"}
    
    def _create_stripe_payment(self, plan, user_id):
        """Create a Stripe payment
        
        Args:
            plan (dict): The subscription plan
            user_id (int): The user ID
            
        Returns:
            dict: Payment information including URL for checkout
        """
        try:
            # In a real app, this would create a Stripe checkout session
            # For now, we'll just return a mock response
            return {
                "success": True,
                "payment_id": f"stripe_{int(time.time())}",
                "checkout_url": f"/mock-stripe-checkout?plan={plan['name']}&price={plan['price']}"
            }
        except Exception as e:
            logger.error(f"Stripe payment error: {str(e)}")
            return {"error": str(e)}
    
    def _create_paypal_payment(self, plan, user_id):
        """Create a PayPal payment
        
        Args:
            plan (dict): The subscription plan
            user_id (int): The user ID
            
        Returns:
            dict: Payment information including URL for checkout
        """
        try:
            # In a real app, this would create a PayPal payment
            # For now, we'll just return a mock response
            return {
                "success": True,
                "payment_id": f"paypal_{int(time.time())}",
                "checkout_url": f"/mock-paypal-checkout?plan={plan['name']}&price={plan['price']}"
            }
        except Exception as e:
            logger.error(f"PayPal payment error: {str(e)}")
            return {"error": str(e)}
    
    def activate_subscription(self, user_id, plan_id, payment_id):
        """Activate a subscription after successful payment
        
        Args:
            user_id (int): The user ID
            plan_id (str): The subscription plan ID
            payment_id (str): The payment ID from the payment processor
            
        Returns:
            bool: True if activation was successful, False otherwise
        """
        try:
            from web.database import db
            from web.models import Subscription
            from datetime import datetime, timedelta
            
            # Calculate expiration date (1 month from now)
            expires_at = datetime.utcnow() + timedelta(days=30)
            
            # Create or update subscription
            subscription = Subscription.query.filter_by(user_id=user_id).first()
            if not subscription:
                subscription = Subscription(
                    user_id=user_id,
                    plan_id=plan_id,
                    status='active',
                    payment_id=payment_id,
                    expires_at=expires_at
                )
                db.session.add(subscription)
            else:
                subscription.plan_id = plan_id
                subscription.status = 'active'
                subscription.payment_id = payment_id
                subscription.expires_at = expires_at
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Subscription activation error: {str(e)}")
            return False
    
    def cancel_subscription(self, user_id):
        """Cancel a user's subscription
        
        Args:
            user_id (int): The user ID
            
        Returns:
            bool: True if cancellation was successful, False otherwise
        """
        try:
            from web.database import db
            from web.models import Subscription
            
            subscription = Subscription.query.filter_by(user_id=user_id).first()
            if subscription:
                subscription.status = 'cancelled'
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Subscription cancellation error: {str(e)}")
            return False