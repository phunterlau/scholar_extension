import requests
from config import jena_reader_api_key, config_dict, client

def get_raw_content(input_url):
    url = f"https://r.jina.ai/{input_url}"
    headers = {"Authorization": f"Bearer {jena_reader_api_key}"} if jena_reader_api_key else {}
    response = requests.get(url, headers=headers)
    return response.text

def generate_summary(content):
    response = client.chat.completions.create(
        model=config_dict['model'],
        messages=[
            {"role": "system", "content": "Summarize the following text from a scientific article in 200 words:"},
            {"role": "user", "content": content[:4000]}
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
    return response.choices[0].message.content