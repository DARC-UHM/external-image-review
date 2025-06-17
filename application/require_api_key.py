from functools import wraps

from flask import current_app, jsonify, request

from application.get_request_ip import get_request_ip


def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        provided_api_key = request.headers.get('API-Key')
        if provided_api_key == current_app.config.get('API_KEY'):
            return func(*args, **kwargs)
        else:
            current_app.logger.warning(f'UNAUTHORIZED API ATTEMPT - IP Address: {get_request_ip()}')
            current_app.logger.info(f'URL: {request.url}')
            return jsonify({'error': 'Unauthorized'}), 401
    return wrapper
