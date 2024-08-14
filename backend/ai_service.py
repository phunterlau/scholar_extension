import yaml
import json
from openai import OpenAI
from groq import Groq
import os
import requests

# Load the configuration
config_openai_dict = {'endpoint': "openai", 'model': "gpt-4o-mini", 'api_key': os.environ.get("OPENAI_API_KEY")}
config_groq_dict = {'endpoint': "groq", 'model': "gemma2-9b-it", 'api_key': os.environ.get("GROQ_API_KEY")}
config_dict = config_openai_dict

if config_dict['endpoint'] == "openai":
    client = OpenAI(api_key=config_dict['api_key'])
elif config_dict['endpoint'] == "groq":
    client = Groq(api_key=config_dict['api_key'])

def load_prompts():
    try:
        with open('prompts.yaml', 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print("prompts.yaml file not found. Please ensure it exists in the correct location.")
        return {}
    except yaml.YAMLError as e:
        print(f"Error parsing prompts.yaml: {e}")
        return {}

prompts = load_prompts()

def get_raw_content(input_url):
    url = f"https://r.jina.ai/{input_url}"
    api_key = os.environ.get('JENA_READER_API_KEY')
    
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return "Error loading text"
    return response.text

def generate_summary(content):
    use_json_mode = config_dict['endpoint'] == "openai"
    
    if content == "Error loading text":
        if use_json_mode:
            return {
                "summary": "Error loading text",
                "mind_map": {
                    "central_topic": "Error",
                    "branches": []
                }
            }
        else:
            return {"summary": "Error loading text", "mind_map": {}}
    
    if use_json_mode:
        messages = [
            {"role": "system", "content": prompts['summary']['system_json']},
            {"role": "user", "content": prompts['summary']['user'].format(content=content[:4000])}
        ]
        response = client.chat.completions.create(
            model=config_dict['model'],
            response_format={"type": "json_object"},
            messages=messages
        )
        return json.loads(response.choices[0].message.content)
    else:
        messages = [
            {"role": "system", "content": prompts['summary']['system_text']},
            {"role": "user", "content": prompts['summary']['user'].format(content=content[:4000])}
        ]
        response = client.chat.completions.create(
            model=config_dict['model'],
            messages=messages
        )
        summary = response.choices[0].message.content
        return {"summary": summary, "mind_map": {}}

def generate_overall_summary(summaries, search_query, links):
    use_json_mode = config_dict['endpoint'] == "openai"
    
    # Combine summaries with their indices and links
    indexed_summaries = [f"{i+1}. {summary}\nSource: {links[i]}" for i, summary in enumerate(summaries) if summary != "Error loading text"]
    combined_summaries = "\n\n".join(indexed_summaries)
    
    if use_json_mode:
        messages = [
            {"role": "system", "content": prompts['overall_summary']['system_json']},
            {"role": "user", "content": prompts['overall_summary']['user'].format(
                search_query=search_query,
                combined_summaries=combined_summaries
            )}
        ]
        response = client.chat.completions.create(
            model=config_dict['model'],
            response_format={"type": "json_object"},
            messages=messages
        )
        return json.loads(response.choices[0].message.content)
    else:
        messages = [
            {"role": "system", "content": prompts['overall_summary']['system_text']},
            {"role": "user", "content": prompts['overall_summary']['user'].format(
                search_query=search_query,
                combined_summaries=combined_summaries
            )}
        ]
        response = client.chat.completions.create(
            model=config_dict['model'],
            messages=messages
        )
        overall_summary = response.choices[0].message.content
        return {
            "overall_summary": overall_summary,
            "followup_questions": [],
            "more_keywords": [],
            "mind_map": {}
        }
