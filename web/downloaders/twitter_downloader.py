import os
import time
import re
from .base_downloader import BaseDownloader
from web.utils.ytdlp_helper import download_with_ytdlp

class TwitterDownloader(BaseDownloader):
    """Twitter video downloader implementation"""
    
    def __init__(self):
        super().__init__()
        self.platform = "Twitter"
    
    def download(self, url, save_path=None, quality="Best", progress_callback=None, status_callback=None, cancel_check=None, extra_opts=None):
        """Download video from Twitter
        
        Args:
            url (str): The Twitter video URL
            save_path (str): The directory to save the downloaded video
            quality (str): The desired quality of the video
            progress_callback (callable): Function to call with progress updates (0-100)
            status_callback (callable): Function to call with status updates
            cancel_check (callable): Function to check if download should be cancelled
            extra_opts (dict): Extra options to pass to the downloader
            
        Returns:
            str: Path to the downloaded file, or None if download failed
        """
        try:
            # Clean the URL to ensure it's valid
            url = self._clean_url(url)
            
            # Extract tweet ID from URL (simplified)
            tweet_id = url.split('/')[-1] if '/' in url else "unknown"
            
            # Generate a title from the tweet ID
            title = f"Twitter Video {tweet_id}"
            
            # Generate filename
            filename = self.generate_filename(title)
            
            # Ensure output path exists
            if not save_path:
                save_path = os.path.join(os.getcwd(), "downloads")
            os.makedirs(save_path, exist_ok=True)
            
            final_path = download_with_ytdlp(
                url=url,
                save_path=save_path,
                platform_name=self.platform,
                quality=quality,
                progress_callback=progress_callback,
                status_callback=status_callback,
                cancel_check=cancel_check,
                extra_opts=extra_opts or {},
            )
            return final_path
                
        except Exception as e:
            if status_callback:
                status_callback(f"Error: {str(e)}")
            return None
            
    def _clean_url(self, url):
        """Clean and validate Twitter URL
        
        Args:
            url (str): The Twitter video URL
            
        Returns:
            str: Cleaned URL
        """
        # Remove query parameters
        url = url.split('?')[0]
        
        # Ensure URL is a Twitter URL
        if not ('twitter.com' in url or 'x.com' in url):
            raise ValueError("Not a valid Twitter URL")
            
        return url
