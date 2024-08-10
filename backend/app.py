from flask import Flask, request, jsonify, Response, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from cachelib import SimpleCache
import json
import io
import uuid

import datetime
import jwt

from config import JWT_SECRET
from database import init_db, get_from_cache, save_to_cache, clear_expired_cache
from ai_service import get_raw_content, generate_summary, generate_overall_summary
from utils import token_required, sanitize_filename, update_link_frequency

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

app = Flask(__name__)
app.secret_key = JWT_SECRET
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1 per 30 seconds"],
    storage_uri="memory://"
)

limiter.request_filter(lambda: request.method == "OPTIONS")

cache = SimpleCache()

# Set up the scheduler to run at 3:00 AM every day
scheduler = BackgroundScheduler()
scheduler.add_job(func=clear_expired_cache, trigger=CronTrigger(hour=3, minute=0))
scheduler.start()

@app.route('/get_token', methods=['POST', 'OPTIONS'])
@limiter.exempt
def get_token():
    if request.method == 'OPTIONS':
        return '', 204
    unique_id = request.json.get('uniqueId')
    if not unique_id:
        return jsonify({'message': 'Unique ID is required'}), 400
    
    token = jwt.encode({
        'sub': unique_id,
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }, JWT_SECRET, algorithm='HS256')
    
    return jsonify({'token': token})

@app.route('/summarize', methods=['POST', 'OPTIONS'])
@limiter.limit("1 per 30 seconds", error_message='Rate limit exceeded')
@token_required
def summarize():
    if request.method == 'OPTIONS':
        return '', 204
    data = request.json
    contents = data['contents']
    search_query = data['searchQuery']
    page_number = data.get('pageNumber', 1)

    token = str(uuid.uuid4())

    def generate():
        summaries = [""]
        total = len(contents)
        markdown_content = f"# Google Scholar Search Results Summary\n\n## Search Query: {search_query}\n\n## Page Number: {page_number}\n\n"
        
        for i, item in enumerate(contents):
            cached_data = get_from_cache(item['link'])
            if cached_data:
                raw_content, summary = cached_data
            else:
                raw_content = get_raw_content(item['link'])
                summary = generate_summary(raw_content)
                if raw_content != "Error loading text" and summary.get('summary') != "Error loading text":
                    save_to_cache(item['link'], raw_content, summary)
            
            summary_text = summary.get('summary', summary) if isinstance(summary, dict) else summary
            if summary_text != "Error loading text":
                summaries.append(summary_text)
                markdown_content += f"### [{item['title']}]({item['link']})\n\n{summary_text}\n\n"
            else:
                markdown_content += f"### [{item['title']}]({item['link']})\n\nError: Unable to load content for this link.\n\n"
            
            progress = (i + 1) / total
            
            yield f"data: {json.dumps({'progress': progress, 'summary': summary_text, 'index': i+1})}\n\n"

        overall_summary = generate_overall_summary(summaries, search_query)
        
        overall_summary_text = overall_summary.get('overall_summary', '')
        followup_questions = overall_summary.get('followup_questions', [])
        more_keywords = overall_summary.get('more_keywords', [])
        mind_map = overall_summary.get('mind_map', {})
        
        markdown_content = f"## Overall Summary\n\n{overall_summary_text}\n\n" + markdown_content
        
        if followup_questions:
            markdown_content += "## Follow-up Questions\n\n"
            for question_data in followup_questions:
                question = question_data['question']
                keywords = question_data['keywords']
                markdown_content += f"- {question}\n"
                markdown_content += f"  Suggested keywords: {', '.join(keywords)}\n\n"
        
        if more_keywords:
            markdown_content += "## More Keywords\n\n"
            markdown_content += ", ".join(more_keywords) + "\n\n"
        
        if mind_map:
            markdown_content += "## Mind Map\n\n"
            markdown_content += f"Central Topic: {mind_map.get('central_topic', '')}\n\n"
            for branch in mind_map.get('branches', []):
                markdown_content += f"- {branch.get('topic', '')}\n"
                for detail in branch.get('details', []):
                    markdown_content += f"  - {detail}\n"
            markdown_content += "\n"
        
        cache.set(token, (markdown_content, search_query, page_number), timeout=1800)

        final_data = {
            'progress': 1, 
            'overall_summary': overall_summary_text, 
            'followup_questions': followup_questions,
            'more_keywords': more_keywords,
            'mind_map': mind_map,
            'token': token
        }
        yield f"data: {json.dumps(final_data)}\n\n"

    return Response(generate(), content_type='text/event-stream')

@app.route('/download_markdown/<token>', methods=['GET'])
@token_required
def download_markdown(token):
    cached_data = cache.get(token)
    
    if cached_data is None:
        return jsonify({"error": "Markdown content not found or expired"}), 404

    markdown_content, search_query, page_number = cached_data
    
    sanitized_query = sanitize_filename(search_query)

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

@app.route('/link_frequency', methods=['GET'])
@token_required
def get_link_frequency():
    conn = sqlite3.connect('cache.db')
    c = conn.cursor()
    c.execute("""
        SELECT lf.url, lf.frequency + COALESCE(c.count, 0) as total_frequency 
        FROM link_frequency lf
        LEFT JOIN (SELECT url, COUNT(*) as count FROM link_counter GROUP BY url) c
        ON lf.url = c.url
        ORDER BY total_frequency DESC LIMIT 100
    """)
    result = c.fetchall()
    conn.close()
    return jsonify([{'url': row[0], 'frequency': row[1]} for row in result])

if __name__ == '__main__':
    init_db()
    app.run(debug=True)