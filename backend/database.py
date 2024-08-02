import sqlite3
from hashlib import md5
from utils import update_link_frequency

def init_db():
    conn = sqlite3.connect('cache.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS cache
                 (url_hash TEXT PRIMARY KEY, url TEXT, raw_content TEXT, summary TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS link_frequency
                 (url_hash TEXT PRIMARY KEY, url TEXT, frequency INTEGER)''')
    conn.commit()
    conn.close()

def get_from_cache(url):
    url_hash = md5(url.encode()).hexdigest()
    conn = sqlite3.connect('cache.db')
    c = conn.cursor()
    c.execute("SELECT raw_content, summary FROM cache WHERE url_hash = ?", (url_hash,))
    result = c.fetchone()
    conn.close()
    update_link_frequency(url)
    return result

def save_to_cache(url, raw_content, summary):
    url_hash = md5(url.encode()).hexdigest()
    conn = sqlite3.connect('cache.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO cache (url_hash, url, raw_content, summary) VALUES (?, ?, ?, ?)",
              (url_hash, url, raw_content, summary))
    conn.commit()
    conn.close()

def batch_update_db(link_counter):
    conn = sqlite3.connect('cache.db')
    c = conn.cursor()
    for url, count in link_counter.items():
        url_hash = md5(url.encode()).hexdigest()
        c.execute("""
            INSERT INTO link_frequency (url_hash, url, frequency)
            VALUES (?, ?, ?)
            ON CONFLICT(url_hash) DO UPDATE SET
            frequency = frequency + ?
        """, (url_hash, url, count, count))
    conn.commit()
    conn.close()