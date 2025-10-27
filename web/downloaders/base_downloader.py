#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base Downloader - Abstract base class for all downloaders
"""

import os
import re
import time
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseDownloader(ABC):
    """Abstract base class for all downloaders"""
    
    def __init__(self):
        """Initialize the base downloader"""
        self.platform_name = "Base"
    
    @abstractmethod
    def download(self, url, save_path, quality="Best", progress_callback=None, status_callback=None, cancel_check=None):
        """Download video or image from the platform
        
        Args:
            url (str): The media URL
            save_path (str): The directory to save the downloaded file
            quality (str): The desired quality of the media
            progress_callback (callable): Function to call with progress updates (0-100)
            status_callback (callable): Function to call with status updates
            cancel_check (callable): Function to check if download should be cancelled
            
        Returns:
            str: Path to the downloaded file, or None if download failed
        """
        pass
    
    def generate_filename(self, title, file_type="video"):
        """Generate a safe filename from the media title
        
        Args:
            title (str): The media title
            file_type (str): Type of file (video, image, audio)
            
        Returns:
            str: A safe filename
        """
        # Remove invalid characters
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
        
        # Limit length
        if len(safe_title) > 100:
            safe_title = safe_title[:100]
        
        # Add platform name and timestamp
        timestamp = int(time.time())
        
        # Determine file extension based on type
        if file_type == "image":
            extension = ".jpg"  # Default for images, will be updated by yt-dlp if needed
        elif file_type == "audio":
            extension = ".mp3"
        else:
            extension = ".mp4"  # Default for videos
            
        filename = f"{safe_title}_{self.platform_name}_{timestamp}{extension}"
        
        return filename
    
    def report_progress(self, percentage, callback=None):
        """Report download progress
        
        Args:
            percentage (float): The download progress percentage (0-100)
            callback (callable): The callback function to report progress to
        """
        if callback:
            callback(int(percentage))
        logger.debug(f"{self.platform_name} download progress: {percentage:.1f}%")
    
    def report_status(self, status, callback=None):
        """Report download status
        
        Args:
            status (str): The status message
            callback (callable): The callback function to report status to
        """
        if callback:
            callback(status)
        logger.info(f"{self.platform_name} status: {status}")
    
    def should_cancel(self, cancel_check=None):
        """Check if download should be cancelled
        
        Args:
            cancel_check (callable): Function to check if download should be cancelled
            
        Returns:
            bool: True if download should be cancelled, False otherwise
        """
        if cancel_check and cancel_check():
            logger.info(f"{self.platform_name} download cancelled")
            return True
        return False
    
    def get_available_qualities(self, url):
        """Get available qualities for the video
        
        Args:
            url (str): The video URL
            
        Returns:
            list: List of available quality options
        """
        # Default implementation returns standard qualities
        return ["Best", "1080p", "720p", "480p", "360p", "Audio Only"]