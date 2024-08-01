import sqlite3
import sys

def view_cache_content(limit=None, search_term=None):
    conn = sqlite3.connect('cache.db')
    c = conn.cursor()

    if search_term:
        query = """
        SELECT c.url, c.raw_content, c.summary, COALESCE(lf.frequency, 0) as frequency
        FROM cache c
        LEFT JOIN link_frequency lf ON c.url_hash = lf.url_hash
        WHERE c.url LIKE ? OR c.raw_content LIKE ? OR c.summary LIKE ?
        ORDER BY c.url
        """
        params = ('%' + search_term + '%',) * 3
    else:
        query = """
        SELECT c.url, c.raw_content, c.summary, COALESCE(lf.frequency, 0) as frequency
        FROM cache c
        LEFT JOIN link_frequency lf ON c.url_hash = lf.url_hash
        ORDER BY c.url
        """
        params = ()

    if limit:
        query += f" LIMIT {limit}"

    c.execute(query, params)
    rows = c.fetchall()

    if not rows:
        print("No entries found in the cache.")
        return

    for i, (url, raw_content, summary, frequency) in enumerate(rows, 1):
        print(f"\n--- Entry {i} ---")
        print(f"URL: {url}")
        print(f"Frequency: {frequency}")
        print(f"Raw Content (first 100 characters): {raw_content[:100]}...")
        print(f"Summary: {summary}")
        print("-" * 50)

    print(f"\nTotal entries displayed: {len(rows)}")
    conn.close()

def view_link_frequency(limit=None, search_term=None):
    conn = sqlite3.connect('cache.db')
    c = conn.cursor()

    if search_term:
        query = """
        SELECT url, frequency
        FROM link_frequency
        WHERE url LIKE ?
        ORDER BY frequency DESC
        """
        params = ('%' + search_term + '%',)
    else:
        query = """
        SELECT url, frequency
        FROM link_frequency
        ORDER BY frequency DESC
        """
        params = ()

    if limit:
        query += f" LIMIT {limit}"

    c.execute(query, params)
    rows = c.fetchall()

    if not rows:
        print("No entries found in the link frequency table.")
        return

    for i, (url, frequency) in enumerate(rows, 1):
        print(f"{i}. URL: {url}")
        print(f"   Frequency: {frequency}")
        print("-" * 50)

    print(f"\nTotal entries displayed: {len(rows)}")
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cache_viewer.py [cache|frequency] [limit] [search_term]")
        sys.exit(1)

    view_type = sys.argv[1]
    limit = None
    search_term = None

    if len(sys.argv) > 2:
        try:
            limit = int(sys.argv[2])
        except ValueError:
            search_term = sys.argv[2]

    if len(sys.argv) > 3:
        search_term = sys.argv[3]

    if view_type == 'cache':
        view_cache_content(limit, search_term)
    elif view_type == 'frequency':
        view_link_frequency(limit, search_term)
    else:
        print("Invalid view type. Use 'cache' or 'frequency'.")