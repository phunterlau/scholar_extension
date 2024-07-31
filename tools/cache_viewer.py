import sqlite3
import sys

def view_cache_content(limit=None, search_term=None):
    conn = sqlite3.connect('cache.db')
    c = conn.cursor()

    if search_term:
        query = """
        SELECT url, raw_content, summary 
        FROM cache 
        WHERE url LIKE ? OR raw_content LIKE ? OR summary LIKE ?
        ORDER BY url
        """
        params = ('%' + search_term + '%',) * 3
    else:
        query = "SELECT url, raw_content, summary FROM cache ORDER BY url"
        params = ()

    if limit:
        query += f" LIMIT {limit}"

    c.execute(query, params)
    rows = c.fetchall()

    if not rows:
        print("No entries found in the cache.")
        return

    for i, (url, raw_content, summary) in enumerate(rows, 1):
        print(f"\n--- Entry {i} ---")
        print(f"URL: {url}")
        print(f"Raw Content (first 100 characters): {raw_content[:100]}...")
        print(f"Summary: {summary}")
        print("-" * 50)

    print(f"\nTotal entries displayed: {len(rows)}")
    conn.close()

if __name__ == "__main__":
    limit = None
    search_term = None

    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            search_term = sys.argv[1]

    if len(sys.argv) > 2:
        search_term = sys.argv[2]

    view_cache_content(limit, search_term)