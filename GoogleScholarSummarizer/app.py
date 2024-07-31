from flask import Flask, request, jsonify, Response
from openai import OpenAI
from groq import Groq
import os
import requests
from flask_cors import CORS
import json
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
CORS(app, resources={r"/summarize": {"origins": "chrome-extension://loojlaeieeklhbpngckhcjhcdcobieln"}})

# Initialize the rate limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1 per 30 seconds"],
    storage_uri="memory://"
)

config_openai_dict = {'endpoint': "openai", 'model': "gpt-4o-mini", 'api_key': os.environ.get("OPENAI_API_KEY")}
config_groq_dict = {'endpoint': "groq", 'model': "llama-3.1-8b-instant", 'api_key': os.environ.get("GROQ_API_KEY")}

config_dict = config_openai_dict
#config_dict = config_groq_dict

if config_dict['endpoint'] == "openai":
    client = OpenAI(api_key=config_dict['api_key'])
elif config_dict['endpoint'] == "groq":
    client = Groq(api_key=config_dict['api_key'])

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/summarize', methods=['POST'])
@limiter.limit("1 per 30 seconds", error_message='', on_breach=lambda: jsonify({"error": "Rate limit exceeded"}))
def summarize():
    data = request.json
    contents = data['contents']
    search_query = data['searchQuery']

    def generate():
        summaries = [""]  # JS took index 1, so we need to add an empty string to index 0
        total = len(contents)
        
        for i, item in enumerate(contents):
            summary = generate_summary(item['link'])
            summaries.append(summary)
            progress = (i + 1) / total
            yield f"data: {json.dumps({'progress': progress, 'summary': summary, 'index': i+1})}\n\n"

        overall_summary = generate_overall_summary(summaries, search_query)
        yield f"data: {json.dumps({'progress': 1, 'overall_summary': overall_summary})}\n\n"

    return Response(generate(), content_type='text/event-stream')

def get_raw_content(input_url):
    url = f"https://r.jina.ai/{input_url}"
    response = requests.get(url)
    return response.text

def generate_summary(input_url):
    content = get_raw_content(input_url)
    response = client.chat.completions.create(
        model=config_dict['model'],
        messages=[
            {"role": "system", "content": "Summarize the following text from a scientific article in 200 words:"},
            {"role": "user", "content": content[:4000]}  # Limit content to 4000 tokens
        ]
    )
    print(f"finished {input_url}")
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