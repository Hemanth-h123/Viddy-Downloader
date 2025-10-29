#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to update all downloaders to accept extra_opts parameter
"""

import os
import re

# List of downloader files to update
downloaders = [
    'vimeo_downloader.py',
    'dailymotion_downloader.py',
    'pinterest_downloader.py',
    'tiktok_downloader.py',
    'linkedin_downloader.py',
    'twitter_downloader.py',
    'facebook_downloader.py'
]

# Directory containing the downloaders
downloaders_dir = os.path.join('web', 'downloaders')

# Pattern to match the download method signature
pattern = r'def download\(self, url, save_path=None, quality="Best", progress_callback=None, status_callback=None, cancel_check=None\):'

# Replacement with extra_opts parameter
replacement = r'def download(self, url, save_path=None, quality="Best", progress_callback=None, status_callback=None, cancel_check=None, extra_opts=None):'

# Pattern to match the docstring
docstring_pattern = r'"""Download .+?Returns:\s+str: Path to the downloaded file, or None if download failed\s+"""'

# Function to update the docstring
def update_docstring(match):
    docstring = match.group(0)
    if 'extra_opts' not in docstring:
        # Find the position to insert the extra_opts parameter
        lines = docstring.split('\n')
        for i, line in enumerate(lines):
            if 'cancel_check' in line:
                # Insert extra_opts after cancel_check
                lines.insert(i+1, '            extra_opts (dict): Extra options to pass to the downloader')
                break
        return '\n'.join(lines)
    return docstring

# Pattern to match the download_with_ytdlp call
ytdlp_pattern = r'final_path = download_with_ytdlp\(\s+url=url,\s+save_path=save_path[^)]+\)'

# Function to update the download_with_ytdlp call
def update_ytdlp_call(match):
    call = match.group(0)
    if 'extra_opts=extra_opts' not in call:
        # Find the position to insert the extra_opts parameter
        lines = call.split('\n')
        for i, line in enumerate(lines):
            if 'cancel_check=cancel_check' in line:
                # Insert extra_opts after cancel_check
                indent = line.split('cancel_check')[0]
                lines.insert(i+1, f'{indent}extra_opts=extra_opts,')
                break
        return '\n'.join(lines)
    return call

# Update each downloader file
for downloader in downloaders:
    file_path = os.path.join(downloaders_dir, downloader)
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        continue
    
    # Read the file content
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Update the method signature
    updated_content = re.sub(pattern, replacement, content)
    
    # Update the docstring
    updated_content = re.sub(docstring_pattern, update_docstring, updated_content, flags=re.DOTALL)
    
    # Update the download_with_ytdlp call
    updated_content = re.sub(ytdlp_pattern, update_ytdlp_call, updated_content, flags=re.DOTALL)
    
    # Write the updated content back to the file
    with open(file_path, 'w') as f:
        f.write(updated_content)
    
    print(f"Updated {downloader}")

print("All downloaders updated successfully!")