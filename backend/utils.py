import re
import jwt
from functools import wraps
from flask import request, jsonify
from config import JWT_SECRET, counter_lock, link_counter

def update_link_frequency(url):
    with counter_lock:
        link_counter[url] += 1

def sanitize_filename(filename):
    filename = re.sub(r'[^\w\s-]', '', filename)
    filename = re.sub(r'\s+', '-', filename)
    return filename.strip('-')[:50]

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'OPTIONS':
            return jsonify({'message': 'OK'}), 200
        
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Malformed Authorization header'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401
        except Exception:
            return jsonify({'message': 'Error validating token!'}), 401
        
        return f(*args, **kwargs)
    return decorated