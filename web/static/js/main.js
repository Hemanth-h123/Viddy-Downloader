/**
 * ALL-in-one Downloader Web - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize platform detection
    initializePlatformDetection();
    
    // Initialize download progress updates
    initializeDownloadProgress();
    
    // Initialize theme switching
    initializeThemeSwitching();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize platform detection for URL input
 */
function initializePlatformDetection() {
    const urlInput = document.getElementById('url');
    const platformInfo = document.getElementById('platform-info');
    const qualitySelect = document.getElementById('quality');
    
    if (urlInput && platformInfo) {
        urlInput.addEventListener('input', function() {
            const url = this.value.trim();
            if (url) {
                detectPlatform(url, platformInfo, qualitySelect);
            } else {
                platformInfo.innerHTML = '<i class="fas fa-info-circle me-1"></i> Paste a URL to detect the platform';
            }
        });
    }
}

/**
 * Detect platform from URL
 */
function detectPlatform(url, infoElement, qualitySelect) {
    // Simple platform detection based on URL
    if (url.includes('youtube.com') || url.includes('youtu.be')) {
        infoElement.innerHTML = '<i class="fab fa-youtube text-danger me-1"></i> YouTube video detected';
        fetchYouTubeQualities(url, qualitySelect);
    } else if (url.includes('facebook.com') || url.includes('fb.com')) {
        infoElement.innerHTML = '<i class="fab fa-facebook text-primary me-1"></i> Facebook video detected';
    } else if (url.includes('instagram.com')) {
        infoElement.innerHTML = '<i class="fab fa-instagram text-danger me-1"></i> Instagram video detected';
    } else if (url.includes('twitter.com') || url.includes('x.com')) {
        infoElement.innerHTML = '<i class="fab fa-twitter text-info me-1"></i> Twitter video detected';
    } else if (url.includes('tiktok.com')) {
        infoElement.innerHTML = '<i class="fab fa-tiktok text-dark me-1"></i> TikTok video detected';
    } else if (url.includes('vimeo.com')) {
        infoElement.innerHTML = '<i class="fab fa-vimeo-v text-info me-1"></i> Vimeo video detected';
    } else if (url.includes('dailymotion.com') || url.includes('dai.ly')) {
        infoElement.innerHTML = '<i class="fas fa-video text-primary me-1"></i> Dailymotion video detected';
    } else if (url.includes('pinterest.com') || url.includes('pin.it')) {
        infoElement.innerHTML = '<i class="fab fa-pinterest text-danger me-1"></i> Pinterest link detected (image download - may require login)';
    } else if (url.includes('linkedin.com')) {
        infoElement.innerHTML = '<i class="fab fa-linkedin text-primary me-1"></i> LinkedIn video detected';
    } else {
        infoElement.innerHTML = '<i class="fas fa-question-circle text-muted me-1"></i> Unknown platform';
    }
}

/**
 * Fetch available qualities for YouTube videos
 * In a real implementation, this would make an AJAX call to the server
 */
function fetchYouTubeQualities(url, qualitySelect) {
    if (!qualitySelect) return;
    
    // In a real implementation, this would be an AJAX call
    // For now, we'll just simulate it
    console.log('Fetching qualities for:', url);
    
    // This would normally come from the server
    const qualities = ['Best', '1080p', '720p', '480p', '360p', 'Audio Only'];
    
    // Update the quality select options
    qualitySelect.innerHTML = '';
    qualities.forEach(quality => {
        const option = document.createElement('option');
        option.value = quality;
        option.textContent = quality === 'Best' ? 'Best Quality' : quality;
        qualitySelect.appendChild(option);
    });
}

/**
 * Initialize download progress updates
 * In a real implementation, this would use WebSockets or Server-Sent Events
 */
function initializeDownloadProgress() {
    // This would be implemented with WebSockets or Server-Sent Events
    // to get real-time updates from the server
    console.log('Download progress updates initialized');
}

/**
 * Initialize theme switching functionality
 */
function initializeThemeSwitching() {
    const themeSelect = document.getElementById('theme');
    if (themeSelect) {
        themeSelect.addEventListener('change', function() {
            setTheme(this.value);
        });
        
        // Set initial theme
        const currentTheme = localStorage.getItem('theme') || 'system';
        themeSelect.value = currentTheme;
        setTheme(currentTheme);
    }
}

/**
 * Set the application theme
 */
function setTheme(theme) {
    document.body.classList.remove('theme-light', 'theme-dark', 'theme-system');
    document.body.classList.add(`theme-${theme}`);
    localStorage.setItem('theme', theme);
}

/**
 * Handle download cancellation
 */
function cancelDownload(downloadId) {
    if (confirm('Are you sure you want to cancel this download?')) {
        // In a real implementation, this would make an AJAX call to the server
        console.log('Cancelling download:', downloadId);
        
        // This would be handled by the server response
        alert('Download cancelled successfully');
    }
}

/**
 * Handle download retry
 */
function retryDownload(downloadId) {
    // In a real implementation, this would make an AJAX call to the server
    console.log('Retrying download:', downloadId);
    
    // This would be handled by the server response
    alert('Download queued for retry');
}

/**
 * Handle download deletion
 */
function deleteDownload(downloadId) {
    if (confirm('Are you sure you want to delete this download?')) {
        // In a real implementation, this would make an AJAX call to the server
        console.log('Deleting download:', downloadId);
        
        // This would be handled by the server response
        alert('Download deleted successfully');
    }
}