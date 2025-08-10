import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from typing import Optional, Dict, Any

# AWS Cognito Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_USER_POOL_ID = os.getenv('AWS_USER_POOLS_ID')

def verify_cognito_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify AWS Cognito token and return user data"""
    try:
        # For now, we'll decode the token without verification
        # In production, you should verify the token signature with AWS Cognito
        payload = jwt.decode(token, options={"verify_signature": False})
        
        # Extract user information from Cognito token
        # Cognito tokens can have different field names depending on the token type
        user_id = payload.get('sub') or payload.get('user_id')
        
        # Try different possible email field names
        email = (payload.get('email') or 
                payload.get('cognito:username') or 
                payload.get('username') or
                payload.get('preferred_username'))
        
        # Try different possible name field names
        name = (payload.get('name') or 
               payload.get('given_name') or 
               payload.get('cognito:username') or
               email)  # Fallback to email if no name
        
        # Ensure we have required fields
        if not user_id:
            return None
            
        if not email:
            return None
        
        user_data = {
            'user_id': user_id,
            'email': email,
            'name': name,
            'role': 'user'  # Default role
        }
        
        return user_data
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None

def get_token_from_header() -> Optional[str]:
    """Extract token from Authorization header"""
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    return None

def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_header()
        if not token:
            return jsonify({
                'success': False,
                'error': 'Authentication token required'
            }), 401
        
        user_data = verify_cognito_token(token)
        if not user_data:
            return jsonify({
                'success': False,
                'error': 'Invalid or expired token'
            }), 401
        
        # Add user data to request context
        request.current_user = user_data
        return f(*args, **kwargs)
    
    return decorated_function

def require_role(required_role: str):
    """Decorator to require specific role for routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = get_token_from_header()
            if not token:
                return jsonify({
                    'success': False,
                    'error': 'Authentication token required'
                }), 401
            
            user_data = verify_cognito_token(token)
            if not user_data:
                return jsonify({
                    'success': False,
                    'error': 'Invalid or expired token'
                }), 401
            
            if user_data.get('role') != required_role and user_data.get('role') != 'admin':
                return jsonify({
                    'success': False,
                    'error': 'Insufficient permissions'
                }), 403
            
            request.current_user = user_data
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
