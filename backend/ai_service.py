import requests
from config import jena_reader_api_key, config_dict, client
import yaml

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
    headers = {"Authorization": f"Bearer {jena_reader_api_key}"} if jena_reader_api_key else {}
    response = requests.get(url, headers=headers)
    return response.text

def generate_summary(content):
    response = client.chat.completions.create(
        model=config_dict['model'],
        messages=[
            {"role": "system", "content": prompts['summary']['system']},
            {"role": "user", "content": prompts['summary']['user'].format(content=content[:4000])}
        ]
    )
    return response.choices[0].message.content

def generate_overall_summary(summaries, search_query):
    combined_summaries = "\n\n".join(summaries)  # Join summaries with double newline for clarity
    response = client.chat.completions.create(
        model=config_dict['model'],
        messages=[
            {"role": "system", "content": prompts['overall_summary']['system']},
            {"role": "user", "content": prompts['overall_summary']['user'].format(
                search_query=search_query,
                combined_summaries=combined_summaries
            )}
        ]
    )
    return response.choices[0].message.content