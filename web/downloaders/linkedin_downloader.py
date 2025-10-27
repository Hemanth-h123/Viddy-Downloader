import os
import time
import re
from .base_downloader import BaseDownloader
from web.utils.ytdlp_helper import download_with_ytdlp

class LinkedInDownloader(BaseDownloader):
    """LinkedIn video downloader implementation"""
    
    def __init__(self):
        super().__init__()
        self.platform = "LinkedIn"
    
    def download(self, url, save_path=None, quality="Best", progress_callback=None, status_callback=None, cancel_check=None):
        """Download video from LinkedIn
        
        Args:
            url (str): The LinkedIn video URL
            save_path (str): The directory to save the downloaded video
            quality (str): The desired quality of the video
            progress_callback (callable): Function to call with progress updates (0-100)
            status_callback (callable): Function to call with status updates
            cancel_check (callable): Function to check if download should be cancelled
            
        Returns:
            str: Path to the downloaded file, or None if download failed
        """
        try:
            # Clean the URL to ensure it's valid
            url = self._clean_url(url)
            
            # Ensure output path exists
            if not save_path:
                save_path = os.path.join(os.getcwd(), "downloads")
            os.makedirs(save_path, exist_ok=True)
            
            # LinkedIn may require authentication and specific options
            extra_opts = {
                'format': 'best[ext=mp4]/best[height<=720]/best',  # Prefer MP4, limit height
                'writethumbnail': False,  # Skip thumbnail download
            }
            
            final_path = download_with_ytdlp(
                url=url,
                save_path=save_path,
                platform_name=self.platform,
                quality=quality,
                progress_callback=progress_callback,
                status_callback=status_callback,
                cancel_check=cancel_check,
                extra_opts=extra_opts,
            )
            return final_path
                
        except Exception as e:
            if status_callback:
                status_callback(f"Error: {str(e)}")
            return None
            
    def _clean_url(self, url):
        """Clean and validate LinkedIn URL
        
        Args:
            url (str): The LinkedIn video URL
            
        Returns:
            str: Cleaned URL
        """
        # Remove query parameters
        url = url.split('?')[0]
        
        # Ensure URL is a LinkedIn URL
        if not ('linkedin.com' in url):
            raise ValueError("Not a valid LinkedIn URL")
            
        return url
