from flask import render_template, jsonify, request
from werkzeug.exceptions import HTTPException

def page_not_found(e):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'message': 'The requested resource was not found.'
        }), 404
    return render_template('errors/404.html'), 404

def server_error(e):
    """Handle 500 errors"""
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'message': 'An internal server error occurred.'
        }), 500
    return render_template('errors/500.html'), 500

def forbidden(e):
    """Handle 403 errors"""
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'message': 'You do not have permission to access this resource.'
        }), 403
    return render_template('errors/403.html'), 403

def handle_http_exception(e):
    """Handle other HTTP exceptions"""
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'message': e.description or 'An error occurred',
            'code': e.code
        }), e.code
    return render_template('errors/error.html', error=e), e.code
