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
    
    def download(self, url, save_path, quality="Best", progress_callback=None, status_callback=None, cancel_check=None, extra_opts=None):
        """Download video from YouTube
        
        Args:
            url (str): The YouTube URL to download from
            save_path (str): The directory to save the downloaded file
            quality (str): The desired quality of the video
            progress_callback (callable): Function to call with progress updates (0-100)
            status_callback (callable): Function to call with status updates
            cancel_check (callable): Function to check if download should be cancelled
            extra_opts (dict): Extra options to pass to the downloader
            
        Returns:
            str: Path to the downloaded file, or None if download failed
        """
        import os
        import logging
        logger = logging.getLogger(__name__)
        
        clean_url = self._clean_url(url)
        
        if status_callback:
            status_callback("Preparing YouTube download...")
        
        # Enhanced options to handle YouTube bot detection
        youtube_opts = {
            'retries': 20,
            'fragment_retries': 20,
            'extractor_retries': 15,
            'extractor_args': {'youtube': {'skip_webpage': False, 'player_skip': False}},
            'socket_timeout': 60,
            'sleep_interval': 5,  # Wait 5 seconds between retries
            'max_sleep_interval': 10,  # Maximum wait of 10 seconds
            'geo_bypass': True,
            'geo_bypass_country': 'US',
            'no_check_certificate': True,
            'nocheckcertificate': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
            },
        }
        
        # Try multiple cookie sources
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # Check if we're in a production environment (like Render)
        is_production = os.environ.get('RENDER') == 'true' or '/opt/render' in os.path.expanduser('~')
        
        if is_production:
            # In production, don't try to use browser cookies which will fail
            logger.info("Running in production environment, using production-specific settings")
            if status_callback:
                status_callback("Using production download settings...")
            
            # Add production-specific settings
            youtube_opts.update({
                'cookiesfrombrowser': None,  # Don't try browser cookies in production
                'force_generic_extractor': False,
                'extract_flat': True,
                'mark_watched': False,
                'ignoreerrors': True,
                'skip_unavailable_fragments': True,
                'youtube_include_dash_manifest': False,  # Skip DASH manifests
                'youtube_include_hls_manifest': False,   # Skip HLS manifests
            })
            
            # Check for cookies.txt in production locations
            production_cookie_locations = [
                '/app/cookies.txt',
                '/app/youtube_cookies.txt',
                os.path.join(root_dir, 'cookies.txt'),
                os.path.join(root_dir, 'youtube_cookies.txt'),
            ]
            
            for cookie_file in production_cookie_locations:
                if os.path.exists(cookie_file) and os.path.getsize(cookie_file) > 0:
                    youtube_opts['cookiefile'] = cookie_file
                    if status_callback:
                        status_callback(f"Using cookies file: {os.path.basename(cookie_file)}")
                    logger.info(f"Using cookies file for YouTube: {cookie_file}")
                    break
        else:
            # In development, try local cookie files first
            cookie_locations = [
                os.path.join(root_dir, 'cookies.txt'),
                os.path.join(root_dir, 'youtube_cookies.txt'),
                os.path.join(os.path.expanduser('~'), 'cookies.txt'),
                os.path.join(os.path.expanduser('~'), 'youtube_cookies.txt'),
            ]
            
            for cookie_file in cookie_locations:
                if os.path.exists(cookie_file) and os.path.getsize(cookie_file) > 0:
                    youtube_opts['cookiefile'] = cookie_file
                    if status_callback:
                        status_callback(f"Using cookies file: {os.path.basename(cookie_file)}")
                    logger.info(f"Using cookies file for YouTube: {cookie_file}")
                    break
            
            # Try browser cookies if no cookie file found
            if 'cookiefile' not in youtube_opts:
                # Try common browsers in order of popularity
                browsers = ['chrome', 'firefox', 'edge', 'safari', 'opera']
                for browser in browsers:
                    try:
                        youtube_opts['cookiesfrombrowser'] = (browser, None)  # None = default profile
                        if status_callback:
                            status_callback(f"Trying cookies from {browser.title()} browser...")
                        logger.info(f"Attempting to extract cookies from {browser}")
                        
                        # We'll test this browser in the actual download
                        break
                    except Exception as e:
                        logger.warning(f"Failed to extract cookies from {browser}: {str(e)}")
                        continue
        
        # Merge with any extra options provided
        if extra_opts:
            youtube_opts.update(extra_opts)
        
        # First attempt with all options
        try:
            if status_callback:
                status_callback("Starting YouTube download with authentication...")
            
            final_path = download_with_ytdlp(
                url=url,
                save_path=save_path,
                platform_name="YouTube",
                quality=quality,
                progress_callback=progress_callback,
                status_callback=status_callback,
                cancel_check=cancel_check,
                extra_opts=youtube_opts
            )
            
            if final_path:
                return final_path
        except Exception as e:
            error_msg = str(e).lower()
            logger.warning(f"First YouTube download attempt failed: {error_msg}")
            if status_callback:
                status_callback(f"Authentication attempt failed: {str(e)}")
        
        # Second attempt with fallback options (no browser cookies)
        try:
            if status_callback:
                status_callback("Retrying with alternative authentication...")
            
            # Remove browser cookies but keep cookie file if present
            fallback_opts = youtube_opts.copy()
            fallback_opts.pop('cookiesfrombrowser', None)
            
            # Enhanced fallback options for bot detection
            fallback_opts.update({
                'skip_download': False,
                'writesubtitles': False,
                'verbose': True,  # Enable verbose output for debugging
                'force_generic_extractor': False,
                'sleep_requests': 1,  # Sleep between requests
                'max_sleep_interval': 5,
                'ignoreerrors': True,  # Continue on download errors
                'external_downloader_args': ['--max-retries', '10'],
                'postprocessor_args': {
                    'ffmpeg': ['-nostdin', '-loglevel', 'warning']
                }
            })
            
            final_path = download_with_ytdlp(
                url=url,
                save_path=save_path,
                platform_name="YouTube",
                quality=quality,
                progress_callback=progress_callback,
                status_callback=status_callback,
                cancel_check=cancel_check,
                extra_opts=fallback_opts
            )
            
            return final_path
        except Exception as e:
            error_msg = str(e)
            logger.error(f"YouTube download failed completely: {error_msg}")
            
            # Provide more user-friendly error messages
            if "Sign in to confirm you're not a bot" in error_msg:
                friendly_msg = "YouTube detected automated access. We're working on a solution. Please try again later or try a different video."
            elif "could not find chrome cookies database" in error_msg:
                friendly_msg = "Authentication issue in server environment. Please try again later."
            elif "Private video" in error_msg:
                friendly_msg = "This video is private and cannot be downloaded without proper authentication."
            elif "This video is unavailable" in error_msg:
                friendly_msg = "This video is unavailable. It may have been removed or restricted."
            elif "Video unavailable" in error_msg:
                friendly_msg = "This video is unavailable. It may have been removed or restricted."
            elif "This video has been removed" in error_msg:
                friendly_msg = "This video has been removed by the uploader."
            else:
                friendly_msg = f"Download failed: {error_msg}"
                
            if status_callback:
                status_callback(friendly_msg)
                
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