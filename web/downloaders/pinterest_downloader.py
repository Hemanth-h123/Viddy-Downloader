import os
import time
import re
from .base_downloader import BaseDownloader
from web.utils.ytdlp_helper import download_with_ytdlp

class PinterestDownloader(BaseDownloader):
    """Pinterest video downloader implementation"""
    
    def __init__(self):
        super().__init__()
        self.platform = "Pinterest"
    
    def download(self, url, save_path=None, quality="Best", progress_callback=None, status_callback=None, cancel_check=None, extra_opts=None):
        """Download image from Pinterest
        
        Args:
            url (str): The Pinterest image URL
            save_path (str): The directory to save the downloaded image
            quality (str): The desired quality of the image
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
            
            # Ensure output path exists
            if not save_path:
                save_path = os.path.join(os.getcwd(), "downloads")
            os.makedirs(save_path, exist_ok=True)
            
            # Pinterest image download with multiple fallback approaches
            final_path = None
            
            # Try 1: Pinterest extractor with specific image options
            try:
                if status_callback:
                    status_callback("Downloading image from Pinterest...")
                
                extra_opts = {
                    'format': 'best[height<=4096]/best',
                    'writethumbnail': False,
                    'writeinfojson': False,
                }
                
                final_path = download_with_ytdlp(
                    url=url,
                    save_path=save_path,
                    platform_name=self.platform,
                    quality=quality,
                    progress_callback=progress_callback,
                    status_callback=status_callback,
                    cancel_check=cancel_check,
                    media_type="image",
                    extra_opts=extra_opts or {},
                )
            except Exception as e:
                if status_callback:
                    status_callback(f"Pinterest extractor failed: {str(e)}")
            
            # Try 2: Generic extractor if Pinterest-specific failed
            if not final_path:
                try:
                    if status_callback:
                        status_callback("Trying generic image extraction...")
                    
                    extra_opts = {
                        'format': 'best[height<=4096]/best',
                        'writethumbnail': False,
                        'writeinfojson': False,
                        'extract_flat': False,
                    }
                    
                    final_path = download_with_ytdlp(
                        url=url,
                        save_path=save_path,
                        platform_name=self.platform,
                        quality=quality,
                        progress_callback=progress_callback,
                        status_callback=status_callback,
                        cancel_check=cancel_check,
                        media_type="image",
                        extra_opts=extra_opts,
                    )
                except Exception as e2:
                    if status_callback:
                        status_callback(f"Generic extraction also failed: {str(e2)}")
            
            # If still no success, provide helpful error message
            if not final_path:
                error_msg = "Unable to download from Pinterest. Pinterest pins may be private, require login, or the URL format may not be supported. Try accessing the pin directly in your browser while logged in to Pinterest."
                if status_callback:
                    status_callback(error_msg)
                raise Exception(error_msg)
            
            return final_path
                
        except Exception as e:
            if status_callback:
                status_callback(f"Error: {str(e)}")
            return None
            
    def _clean_url(self, url):
        """Clean and validate Pinterest URL
        
        Args:
            url (str): The Pinterest video URL
            
        Returns:
            str: Cleaned URL
        """
        # Remove query parameters
        url = url.split('?')[0]
        
        # Ensure URL is a Pinterest URL
        if not ('pinterest.com' in url or 'pin.it' in url):
            raise ValueError("Not a valid Pinterest URL")
            
        return url
