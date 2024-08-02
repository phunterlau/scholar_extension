import os
from collections import Counter
import threading
from openai import OpenAI
from groq import Groq

JWT_SECRET = os.environ.get('JWT_SECRET', 'your_secure_secret_here')
jena_reader_api_key = os.environ.get('JENA_READER_API_KEY')

config_openai_dict = {'endpoint': "openai", 'model': "gpt-4o-mini", 'api_key': os.environ.get("OPENAI_API_KEY")}
config_groq_dict = {'endpoint': "groq", 'model': "gemma2-9b-it", 'api_key': os.environ.get("GROQ_API_KEY")}
config_dict = config_openai_dict

if config_dict['endpoint'] == "openai":
    client = OpenAI(api_key=config_dict['api_key'])
elif config_dict['endpoint'] == "groq":
    client = Groq(api_key=config_dict['api_key'])

link_counter = Counter()
counter_lock = threading.Lock()