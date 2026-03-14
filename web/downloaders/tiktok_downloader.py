import os
import time
import re
from web.downloaders.base_downloader import BaseDownloader
from web.utils.ytdlp_helper import download_with_ytdlp

class TikTokDownloader(BaseDownloader):
    """TikTok video downloader implementation"""
    
    def __init__(self):
        super().__init__()
        self.platform = "TikTok"
    
    def download(self, url, save_path, quality="Best", progress_callback=None, status_callback=None, cancel_check=None, extra_opts=None, media_type="video"):
        """Download video from TikTok"""
        try:
            # Clean the URL to ensure it's valid
            url = self._clean_url(url)
            
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
                media_type=media_type,
            )
            return final_path
                
        except Exception as e:
            if status_callback:
                status_callback(f"Error: {str(e)}")
            return None
            
    def _clean_url(self, url):
        """Clean and validate TikTok URL"""
        # Remove query parameters
        url = url.split('?')[0]
        
        # Ensure URL is a TikTok URL
        if not ('tiktok.com' in url):
            raise ValueError("Not a valid TikTok URL")
            
        return url
