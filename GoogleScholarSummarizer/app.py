from flask import Flask, request, jsonify
# OpenAI or Groq or local models from Chrome or iOS in future
from openai import OpenAI
from groq import Groq
import os
import requests

from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/summarize": {"origins": "chrome-extension://loojlaeieeklhbpngckhcjhcdcobieln"}})

# cheap and fast gpt-4o-mini
config_openai_dict = {'endpoint': "openai", 'model': "gpt-4o-mini", 'api_key': os.environ.get("OPENAI_API_KEY")}
# Llama 3.1 8b is very fast, but the prompt needs some tuning.
config_groq_dict = {'endpoint': "groq", 'model': "llama-3.1-8b-instant", 'api_key': os.environ.get("GROQ_API_KEY")}

# switch between OpenAI/GPT and Groq/Llama 3.1
#config_dict = config_groq_dict
config_dict = config_openai_dict

if config_dict['endpoint'] == "openai":
    client = OpenAI(
        api_key=config_dict['api_key']
    )
elif config_dict['endpoint'] == "groq":
    client = Groq(
        api_key=config_dict['api_key']
    )

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/summarize', methods=['POST'])
def summarize():
    data = request.json
    contents = data['contents']
    search_query = data['searchQuery']
    # contents dictionary has a list of URLs and the "contents" value is empty

    summaries = [""] # JS took index 1, so we need to add an empty string to index 0
    for item in contents:
        summary = generate_summary(item['link'])
        summaries.append(summary)

    overall_summary = generate_overall_summary(summaries, search_query)

    return jsonify({
        'summaries': summaries,
        'overallSummary': overall_summary
    })

# for each url, add a "https://r.jina.ai/" prefix and use requests to get its content
# for example https://r.jina.ai/https://arxiv.org/abs/2406.02450
def get_raw_content(input_url):
    url = f"https://r.jina.ai/{input_url}"
    response = requests.get(url)
    return response.text

# for each url link, get the raw content and summarize each content
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