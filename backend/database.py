import sqlite3
from hashlib import md5
from utils import update_link_frequency
import datetime
import json

def init_db():
    conn = sqlite3.connect('cache.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS cache
                 (url_hash TEXT PRIMARY KEY, url TEXT, raw_content TEXT, summary TEXT, date_cached TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS link_frequency
                 (url_hash TEXT PRIMARY KEY, url TEXT, frequency INTEGER)''')
    conn.commit()
    conn.close()

def get_from_cache(url):
    url_hash = md5(url.encode()).hexdigest()
    conn = sqlite3.connect('cache.db')
    c = conn.cursor()
    c.execute("SELECT raw_content, summary, date_cached FROM cache WHERE url_hash = ?", (url_hash,))
    result = c.fetchone()
    conn.close()

    if result:
        raw_content, summary_json, date_cached = result
        current_date = datetime.date.today()
        cached_date = datetime.datetime.strptime(date_cached, "%Y-%m-%d").date()
        if (current_date - cached_date).days <= 7:
            update_link_frequency(url)
            return raw_content, json.loads(summary_json)
    
    return None

def save_to_cache(url, raw_content, summary):
    url_hash = md5(url.encode()).hexdigest()
    date_cached = datetime.date.today().isoformat()
    summary_json = json.dumps(summary)
    conn = sqlite3.connect('cache.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO cache (url_hash, url, raw_content, summary, date_cached) VALUES (?, ?, ?, ?, ?)",
              (url_hash, url, raw_content, summary_json, date_cached))
    conn.commit()
    conn.close()


def clear_expired_cache():
    expiration_date = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    conn = sqlite3.connect('cache.db')
    c = conn.cursor()
    c.execute("DELETE FROM cache WHERE date_cached < ?", (expiration_date,))
    conn.commit()
    conn.close()