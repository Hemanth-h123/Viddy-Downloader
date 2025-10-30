#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WSGI entry point for production deployment
"""

import os
from app import app

if __name__ == "__main__":
    # Get port from environment variable for production environments like Render
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)