from flask import Flask, request, jsonify, Response, send_file
from openai import OpenAI
from groq import Groq
import os
import requests
from flask_cors import CORS
import json
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sqlite3
from hashlib import md5
import io
import uuid
from cachelib import SimpleCache
import jwt
from functools import wraps
import re
import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Set a secret key for sessions
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Initialize the rate limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1 per 30 seconds"],
    storage_uri="memory://"
)

# Define a custom error handler for rate limiting
def ratelimit_error_handler(e):
    return jsonify({"error": "Rate limit exceeded"}), 429

limiter.request_filter(lambda: request.method == "OPTIONS")

# Initialize a cache
cache = SimpleCache()

config_openai_dict = {'endpoint': "openai", 'model': "gpt-4o-mini", 'api_key': os.environ.get("OPENAI_API_KEY")}
config_groq_dict = {'endpoint': "groq", 'model': "gemma2-9b-it", 'api_key': os.environ.get("GROQ_API_KEY")}

config_dict = config_openai_dict
#config_dict = config_groq_dict

if config_dict['endpoint'] == "openai":
    client = OpenAI(api_key=config_dict['api_key'])
elif config_dict['endpoint'] == "groq":
    client = Groq(api_key=config_dict['api_key'])

jena_reader_api_key = os.environ.get('JENA_READER_API_KEY')

# Secret key for JWT - store this securely and don't expose it
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key')

@app.route('/get_token', methods=['POST'])
def get_token():
    unique_id = request.json.get('uniqueId')
    if not unique_id:
        return jsonify({'message': 'Unique ID is required'}), 400
    
    # Generate a JWT
    token = jwt.encode({
        'sub': unique_id,
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }, JWT_SECRET, algorithm='HS256')
    
    return jsonify({'token': token})

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('cache.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS cache
                 (url_hash TEXT PRIMARY KEY, url TEXT, raw_content TEXT, summary TEXT)''')
    conn.commit()
    conn.close()

init_db()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'OPTIONS':
            return jsonify({'message': 'OK'}), 200
        
        print("Headers:", request.headers)  # Print all headers
        
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            print("Authorization header:", auth_header)  # Print the Authorization header
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                print("Malformed Authorization header")
                return jsonify({'message': 'Malformed Authorization header'}), 401
        
        if not token:
            print("Token is missing")
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            print("Decoded token:", decoded)  # Print the decoded token
        except jwt.ExpiredSignatureError:
            print("Token has expired")
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            print("Invalid token")
            return jsonify({'message': 'Invalid token!'}), 401
        
        return f(*args, **kwargs)
    return decorated

def get_from_cache(url):
    url_hash = md5(url.encode()).hexdigest()
    conn = sqlite3.connect('cache.db')
    c = conn.cursor()
    c.execute("SELECT raw_content, summary FROM cache WHERE url_hash = ?", (url_hash,))
    result = c.fetchone()
    conn.close()
    return result

def save_to_cache(url, raw_content, summary):
    url_hash = md5(url.encode()).hexdigest()
    conn = sqlite3.connect('cache.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO cache (url_hash, url, raw_content, summary) VALUES (?, ?, ?, ?)",
              (url_hash, url, raw_content, summary))
    conn.commit()
    conn.close()

def sanitize_filename(filename):
    # Remove any non-word characters (everything except numbers and letters)
    filename = re.sub(r'[^\w\s-]', '', filename)
    # Replace all runs of whitespace with a single dash
    filename = re.sub(r'\s+', '-', filename)
    return filename.strip('-')[:50]  # Trim to 50 characters max

@app.route('/summarize', methods=['POST', 'OPTIONS'])
@limiter.limit("1 per 30 seconds", error_message='Rate limit exceeded')
@token_required
def summarize():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'OK'}), 200
    data = request.json
    contents = data['contents']
    search_query = data['searchQuery']
    page_number = data.get('pageNumber', 1)

    # Generate a unique token for this summarization request
    token = str(uuid.uuid4())

    def generate():
        summaries = [""]  # JS took index 1, so we need to add an empty string to index 0
        total = len(contents)
        markdown_content = f"# Google Scholar Search Results Summary\n\n## Search Query: {search_query}\n\n## Page Number: {page_number}\n\n"
        
        for i, item in enumerate(contents):
            cached_data = get_from_cache(item['link'])
            if cached_data:
                raw_content, summary = cached_data
            else:
                raw_content = get_raw_content(item['link'])
                summary = generate_summary(raw_content)
                save_to_cache(item['link'], raw_content, summary)
            
            summaries.append(summary)
            markdown_content += f"### [{item['title']}]({item['link']})\n\n{summary}\n\n"
            progress = (i + 1) / total
            yield f"data: {json.dumps({'progress': progress, 'summary': summary, 'index': i+1})}\n\n"

        overall_summary = generate_overall_summary(summaries, search_query)
        markdown_content = f"## Overall Summary\n\n{overall_summary}\n\n" + markdown_content
        
        # Store the markdown content in the short life cache with the token as the key
        cache.set(token, (markdown_content, search_query, page_number), timeout=1800) 

        yield f"data: {json.dumps({'progress': 1, 'overall_summary': overall_summary, 'token': token})}\n\n"

    return Response(generate(), content_type='text/event-stream')

@app.route('/download_markdown/<token>', methods=['GET', 'OPTIONS'])
@token_required
def download_markdown(token):
    if request.method == 'OPTIONS':
        return jsonify({'message': 'OK'}), 200
    cached_data = cache.get(token)
    
    if cached_data is None:
        return jsonify({"error": "Markdown content not found or expired"}), 404

    markdown_content, search_query, page_number = cached_data
    
    sanitized_query = sanitize_filename(search_query)

    # Create a BytesIO object and write the markdown content to it
    buffer = io.BytesIO()
    buffer.write(markdown_content.encode())
    buffer.seek(0)

    filename = f'scholar_summary-{sanitized_query}-page{page_number}.md'
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='text/markdown'
    )

def get_raw_content(input_url):
    url = f"https://r.jina.ai/{input_url}"
    api_key = jena_reader_api_key
    
    if api_key:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(url, headers=headers)
    else:
        response = requests.get(url)
    
    return response.text

def generate_summary(content):
    response = client.chat.completions.create(
        model=config_dict['model'],
        messages=[
            {"role": "system", "content": "Summarize the following text from a scientific article in 200 words:"},
            {"role": "user", "content": content[:4000]}  # Limit content to 4000 tokens
        ]
    )
    return response.choices[0].message.content

def generate_overall_summary(summaries, search_query):
    combined_summaries = " ".join(summaries)
    response = client.chat.completions.create(
        model=config_dict['model'],
        messages=[
            {"role": "system", "content": f"Given the Google Scholar search query '{search_query}', summarize the following summaries from scientific research article summaries in 200 words:"},
            {"role": "user", "content": combined_summaries}
        ]
    )
    output = response.choices[0].message.content
    print(output)
    return output

if __name__ == '__main__':
    app.run(debug=True)