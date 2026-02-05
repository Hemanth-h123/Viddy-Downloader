#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Downloader module for the web application
"""

import re
import os
from urllib.parse import urlparse

# Import downloader implementations
from web.downloaders.youtube_downloader import YouTubeDownloader
from web.downloaders.facebook_downloader import FacebookDownloader
from web.downloaders.instagram_downloader import InstagramDownloader
from web.downloaders.twitter_downloader import TwitterDownloader
from web.downloaders.tiktok_downloader import TikTokDownloader
from web.downloaders.vimeo_downloader import VimeoDownloader
from web.downloaders.dailymotion_downloader import DailymotionDownloader
from web.downloaders.pinterest_downloader import PinterestDownloader
from web.downloaders.linkedin_downloader import LinkedInDownloader


def identify_platform(url):
    """Identify the social media platform from a URL
    
    Args:
        url (str): The URL to analyze
        
    Returns:
        str: The platform name, or None if not recognized
    """
    if not url:
        return None
        
    # Parse the URL
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    
    # Check for YouTube
    if 'youtube.com' in domain or 'youtu.be' in domain:
        return 'youtube'
    
    # Check for Facebook
    elif 'facebook.com' in domain or 'fb.com' in domain or 'fb.watch' in domain:
        return 'facebook'
    
    # Check for Instagram
    elif 'instagram.com' in domain:
        return 'instagram'
    
    # Check for Twitter
    elif 'twitter.com' in domain or 'x.com' in domain:
        return 'twitter'
    
    # Check for TikTok
    elif 'tiktok.com' in domain:
        return 'tiktok'
    
    # Check for Vimeo
    elif 'vimeo.com' in domain:
        return 'vimeo'
    
    # Check for Dailymotion
    elif 'dailymotion.com' in domain or 'dai.ly' in domain:
        return 'dailymotion'
    
    # Check for Pinterest (limited support - mostly images, not videos)
    elif 'pinterest.com' in domain or 'pin.it' in domain:
        return 'pinterest'
    
    # Check for LinkedIn
    elif 'linkedin.com' in domain:
        return 'linkedin'
    
    # Unknown platform
    return None


def get_downloader(platform):
    """Get the appropriate downloader for the given platform
    
    Args:
        platform (str): The platform name (youtube, facebook, etc.)
        
    Returns:
        Downloader: An instance of the appropriate downloader class
    """
    platform = platform.lower()
    
    if platform == "youtube":
        # Allow suspension via environment variable
        if os.environ.get('SUSPEND_YOUTUBE', '').lower() == 'true':
            return None
        return YouTubeDownloader()
    elif platform == "facebook":
        return FacebookDownloader()
    elif platform == "instagram":
        return InstagramDownloader()
    elif platform == "twitter":
        return TwitterDownloader()
    elif platform == "tiktok":
        return TikTokDownloader()
    elif platform == "vimeo":
        return VimeoDownloader()
    elif platform == "dailymotion":
        return DailymotionDownloader()
    elif platform == "pinterest":
        return PinterestDownloader()
    elif platform == "linkedin":
        return LinkedInDownloader()
    else:
        return None
