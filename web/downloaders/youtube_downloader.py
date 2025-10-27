#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YouTube Downloader - Implementation for downloading videos from YouTube
"""

import os
import pytube
from web.downloaders.base_downloader import BaseDownloader
from web.utils.ytdlp_helper import download_with_ytdlp


class YouTubeDownloader(BaseDownloader):
    """YouTube video downloader implementation"""
    
    def __init__(self):
        """Initialize the YouTube downloader"""
        super().__init__()
        self.platform_name = "YouTube"
    
    def download(self, url, save_path, quality="Best", progress_callback=None, status_callback=None, cancel_check=None):
        """Download video from YouTube
        
        Args:
            url (str): The YouTube video URL
            save_path (str): The directory to save the downloaded video
            quality (str): The desired quality of the video
            progress_callback (callable): Function to call with progress updates (0-100)
            status_callback (callable): Function to call with status updates
            cancel_check (callable): Function to check if download should be cancelled
            
        Returns:
            str: Path to the downloaded file, or None if download failed
        """
        try:
            url = self._clean_url(url)
            if status_callback:
                status_callback("Preparing download...")
            final_path = download_with_ytdlp(
                url=url,
                save_path=save_path,
                platform_name=self.platform_name,
                quality=quality,
                progress_callback=progress_callback,
                status_callback=status_callback,
                cancel_check=cancel_check,
            )
            return final_path
        except Exception:
            return None
            
    def _clean_url(self, url):
        """Clean and validate YouTube URL
        
        Args:
            url (str): The YouTube URL to clean
            
        Returns:
            str: Cleaned URL
        """
        # Basic validation
        if not url:
            raise ValueError("URL cannot be empty")
            
        # Handle common YouTube URL formats
        if 'youtu.be' in url:
            video_id = url.split('/')[-1].split('?')[0]
            return f"https://www.youtube.com/watch?v={video_id}"
        elif 'youtube.com/watch' in url:
            return url
        elif 'youtube.com/shorts' in url:
            video_id = url.split('/')[-1].split('?')[0]
            return f"https://www.youtube.com/watch?v={video_id}"
        else:
            # If it doesn't match known patterns, return as is
            return url
    
    def get_video_info(self, url):
        """Get information about a YouTube video
        
        Args:
            url (str): The YouTube video URL
            
        Returns:
            dict: Video information including title, author, length, etc.
        """
        try:
            yt = pytube.YouTube(url)
            
            # Get video information
            info = {
                'title': yt.title,
                'author': yt.author,
                'length': yt.length,  # in seconds
                'views': yt.views,
                'thumbnail_url': yt.thumbnail_url,
                'publish_date': yt.publish_date.isoformat() if yt.publish_date else None,
                'description': yt.description,
                'available_qualities': [stream.resolution for stream in yt.streams.filter(progressive=True)]
            }
            
            return info
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_available_qualities(self, url):
        """Get available qualities for the YouTube video
        
        Args:
            url (str): The YouTube video URL
            
        Returns:
            list: List of available quality options
        """
        try:
            yt = pytube.YouTube(url)
            
            # Get available resolutions from progressive streams
            resolutions = set()
            for stream in yt.streams.filter(progressive=True):
                if stream.resolution:
                    resolutions.add(stream.resolution)
            
            # Add standard options
            qualities = ["Best"] + sorted(list(resolutions), reverse=True) + ["Audio Only"]
            return qualities
            
        except Exception:
            # Return default qualities if we can't fetch them
            return super().get_available_qualities(url)