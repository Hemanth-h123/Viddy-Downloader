    def download(self, url, save_path, quality="Best", progress_callback=None, status_callback=None, cancel_check=None, extra_opts=None, media_type="video"):
        """Download video or image from YouTube
        
        Args:
            url (str): The YouTube video URL
            save_path (str): The directory to save the downloaded file
            quality (str): The desired quality
            progress_callback (callable): Function to call with progress updates (0-100)
            status_callback (callable): Function to call with status updates
            cancel_check (callable): Function to check if download should be cancelled
            extra_opts (dict): Extra options to pass to the downloader
            media_type (str): The type of media to download (video or image)
            
        Returns:
            str: Path to the downloaded file, or None if download failed
        """
        import os
        import logging
        import tempfile
        logger = logging.getLogger(__name__)
        
        temp_cookie_path = None
        try:
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
            
            # 1. Try user-specific cookies first if provided in extra_opts
            user_cookies = (extra_opts or {}).pop('user_cookies', None)
            if user_cookies:
                try:
                    # Create a temporary file for the user cookies
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tf:
                        tf.write(user_cookies)
                        temp_cookie_path = tf.name
                    
                    youtube_opts['cookiefile'] = temp_cookie_path
                    if status_callback:
                        status_callback("Using your uploaded YouTube cookies...")
                    logger.info(f"Using user-provided cookies from temporary file: {temp_cookie_path}")
                except Exception as e:
                    logger.error(f"Failed to create temporary cookies file: {e}")

            # 2. Check if we're in a production environment (like Render)
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
                
                # Check for cookies.txt in production locations if user-cookies not provided
                if not user_cookies:
                    production_cookie_locations = [
                        '/app/cookies.txt',
                        '/app/youtube_cookies.txt',
                        '/opt/render/project/src/cookies.txt',
                        '/opt/render/project/src/youtube_cookies.txt',
                        '/tmp/cookies.txt',
                        os.path.join(root_dir, 'cookies.txt'),
                        os.path.join(root_dir, 'youtube_cookies.txt'),
                    ]
                    
                    for cookie_file in production_cookie_locations:
                        if os.path.exists(cookie_file) and os.path.getsize(cookie_file) > 0:
                            youtube_opts['cookiefile'] = cookie_file
                            if status_callback:
                                status_callback(f"Using system cookies file: {os.path.basename(cookie_file)}")
                            logger.info(f"Using system cookies file for YouTube: {cookie_file}")
                            break
            else:
                # In development, try local cookie files first if user-cookies not provided
                if not user_cookies:
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
                                status_callback(f"Using local cookies file: {os.path.basename(cookie_file)}")
                            logger.info(f"Using local cookies file for YouTube: {cookie_file}")
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
                    url=clean_url,
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
            
            # Second attempt with fallback options (no browser cookies, potentially no cookies at all)
            try:
                if status_callback:
                    status_callback("Retrying with alternative authentication...")
                
                fallback_opts = youtube_opts.copy()
                fallback_opts.pop('cookiesfrombrowser', None)
                # Keep user-uploaded cookiefile if present, otherwise fallback
                if not user_cookies:
                    fallback_opts.pop('cookiefile', None)
                
                # Enhanced fallback options for bot detection
                fallback_opts.update({
                    'skip_download': False,
                    'writesubtitles': False,
                    'verbose': True,
                    'force_generic_extractor': False,
                    'sleep_requests': 1,
                    'max_sleep_interval': 5,
                    'ignoreerrors': True,
                    'external_downloader_args': ['--max-retries', '10'],
                    'postprocessor_args': {
                        'ffmpeg': ['-nostdin', '-loglevel', 'warning']
                    }
                })
                
                final_path = download_with_ytdlp(
                    url=clean_url,
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
                    friendly_msg = "YouTube detected automated access. Please upload a fresh cookies.txt file in your Settings to bypass this."
                elif "could not find chrome cookies database" in error_msg:
                    friendly_msg = "Authentication issue in server environment. Please try again later."
                elif "Private video" in error_msg:
                    friendly_msg = "This video is private. Try uploading your cookies.txt in Settings to access it."
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
        except Exception as e:
            logger.error(f"Unexpected error in YouTube downloader: {e}")
            return None
        finally:
            # Clean up temporary cookie file if it was created
            if temp_cookie_path and os.path.exists(temp_cookie_path):
                try:
                    os.remove(temp_cookie_path)
                    logger.info(f"Deleted temporary user cookies file: {temp_cookie_path}")
                except Exception as e:
                    logger.error(f"Failed to delete temporary cookies file: {e}")
