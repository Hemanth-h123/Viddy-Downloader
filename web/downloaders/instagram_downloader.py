import os
import time
import logging
import platform
import sys
from urllib.parse import urlparse
from .base_downloader import BaseDownloader
from web.utils.ytdlp_helper import download_with_ytdlp

logger = logging.getLogger(__name__)

class InstagramDownloader(BaseDownloader):
    def __init__(self):
        super().__init__()
        self.platform_name = "Instagram"
        print("Using web/downloaders/instagram_downloader.py")

    def extract_shortcode(self, url):
        """Extract the Instagram post shortcode from the URL."""
        parsed = urlparse(url)
        path = parsed.path.strip('/').split('/')
        if path and path[-1]:
            return path[-1].split('?')[0]
        return None
        
    def is_production_environment(self):
        """Check if running in a production environment like Render."""
        # Check for environment variables or container indicators
        if os.environ.get('RENDER') or os.environ.get('PRODUCTION'):
            return True
        # Check for Docker/container environment
        if os.path.exists('/.dockerenv') or os.path.exists('/run/.containerenv'):
            return True
        return False

    def download(self, url, save_path=None, quality="Best", progress_callback=None, status_callback=None, cancel_check=None, extra_opts=None):
        """Download Instagram content (video or image) from the given URL.
        
        Args:
            url (str): The Instagram content URL
            save_path (str): The directory to save the downloaded content
            quality (str): The desired quality of the content (not used for Instagram)
            progress_callback (callable): Function to call with progress updates (0-100)
            status_callback (callable): Function to call with status updates
            cancel_check (callable): Function to check if download should be cancelled
            extra_opts (dict): Extra options to pass to the downloader
            
        Returns:
            str: Path to the downloaded file, or None if download failed
        """
        try:
            # Enhanced options for Instagram to handle authentication and rate-limiting
            instagram_opts = {
                'retries': 15,
                'fragment_retries': 15,
                'extractor_retries': 10,
                'socket_timeout': 60,
                'sleep_interval': 5,
                'max_sleep_interval': 10,
                'geo_bypass': True,
                'geo_bypass_country': 'US',
                'no_check_certificate': True,
                'nocheckcertificate': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Sec-Fetch-Mode': 'navigate',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Dnt': '1',
                    'Connection': 'keep-alive',
                    'Referer': 'https://www.instagram.com/',
                    'Origin': 'https://www.instagram.com',
                    'Sec-Fetch-Site': 'same-origin',
                    'Sec-Fetch-Dest': 'document',
                    'Upgrade-Insecure-Requests': '1',
                },
                'ignoreerrors': True,
                'skip_unavailable_fragments': True,
                'force_generic_extractor': False,
                'extract_flat': True,
                'mark_watched': False,
                'verbose': True,
                'sleep_requests': 1,
                'external_downloader_args': ['--max-retries', '10'],
                'postprocessor_args': {'ffmpeg': ['-nostdin', '-loglevel', 'warning']},
            }
            
            # Merge with any extra options provided
            if extra_opts:
                instagram_opts.update(extra_opts)
                
            # Production environment specific settings
            if self.is_production_environment():
                if status_callback:
                    status_callback("Running in production environment, using special Instagram settings...")
                
                # Disable browser cookie extraction in production/container environments
                instagram_opts['cookiesfrombrowser'] = None
                
                # Try to use specific cookie files in production
                cookie_paths = [
                    '/tmp/cookies.txt',
                    '/app/cookies.txt',
                    '/opt/render/project/src/cookies.txt',
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'cookies.txt'),
                ]
                
                for cookie_path in cookie_paths:
                    if os.path.exists(cookie_path):
                        instagram_opts['cookies'] = cookie_path
                        if status_callback:
                            status_callback(f"Using cookie file: {cookie_path}")
                        break
            
            # First attempt with full options
            try:
                if status_callback:
                    status_callback("Downloading from Instagram with authentication...")
                
                final_path = download_with_ytdlp(
                    url=url,
                    save_path=save_path or os.getcwd(),
                    platform_name=self.platform_name,
                    quality=quality,
                    progress_callback=progress_callback,
                    status_callback=status_callback,
                    cancel_check=cancel_check,
                    extra_opts=instagram_opts,
                    media_type="auto",  # Auto-detect videos or images
                )
                return final_path
            except Exception as e:
                logger.error(f"First Instagram download attempt failed: {str(e)}")
                if status_callback:
                    status_callback(f"First attempt failed: {str(e)}. Trying alternative method...")
                
                # Second attempt with modified options
                instagram_opts['force_generic_extractor'] = True
                instagram_opts['extract_flat'] = False
                instagram_opts['skip_download'] = False
                instagram_opts['writesubtitles'] = False
                
                final_path = download_with_ytdlp(
                    url=url,
                    save_path=save_path or os.getcwd(),
                    platform_name=self.platform_name,
                    quality=quality,
                    progress_callback=progress_callback,
                    status_callback=status_callback,
                    cancel_check=cancel_check,
                    extra_opts=instagram_opts,
                    media_type="auto",  # Auto-detect videos or images
                )
                return final_path
                
        except Exception as e:
            error_message = str(e)
            logger.error(f"Failed to download Instagram content: {error_message}")
            
            # Provide user-friendly error messages
            if "Requested content is not available" in error_message or "rate-limit reached" in error_message:
                user_message = "Instagram rate limit reached or content requires login. Try again later or use a different URL."
            elif "login required" in error_message:
                user_message = "This Instagram content requires login. Please try a public post instead."
            elif "Browser cookie extraction failed" in error_message:
                user_message = "Could not extract browser cookies. Try logging into Instagram in your browser first."
            else:
                user_message = f"Error: {error_message}"
                
            if status_callback:
                status_callback(user_message)
            return None