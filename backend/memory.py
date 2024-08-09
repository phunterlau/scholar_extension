import sqlite3
import json
from datetime import datetime
import os
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class MemoryManager:
    def __init__(self, db_name='agent_memory.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
        self.summary_cache = {}

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                memory TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS summary_cache (
                user_id TEXT PRIMARY KEY,
                summary TEXT,
                last_memory_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def add_memory(self, user_id, memory):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO memories (user_id, memory) VALUES (?, ?)', 
                       (user_id, memory))
        self.conn.commit()
        return cursor.lastrowid

    def get_recent_memories(self, user_id, limit=5):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, memory FROM memories WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?', 
                       (user_id, limit))
        memories = cursor.fetchall()
        return memories

    def summarize_memories(self, memories):
        memories_text = "\n".join(f"- {memory[1]}" for memory in memories)
        prompt = f"Based on the following recent memories, provide a summary of the user's behavior and characteristics:\n\n{memories_text}\n\nSummary:"
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI assistant that summarizes user memories and behaviors."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            n=1,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    def get_memories(self, user_id):
        recent_memories = self.get_recent_memories(user_id)
        if not recent_memories:
            return {"latest_memory": "No memories found.", "overall_summary": "No memories found."}
        
        latest_memory = recent_memories[0][1]
        latest_memory_id = recent_memories[0][0]

        # Check if we have a cached summary and if it's still valid
        cached_summary = self.get_cached_summary(user_id)
        if cached_summary and cached_summary['last_memory_id'] == latest_memory_id:
            overall_summary = cached_summary['summary']
        else:
            overall_summary = self.summarize_memories(recent_memories)
            self.cache_summary(user_id, overall_summary, latest_memory_id)

        return {"latest_memory": latest_memory, "overall_summary": overall_summary}

    def get_cached_summary(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT summary, last_memory_id FROM summary_cache WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if result:
            return {'summary': result[0], 'last_memory_id': result[1]}
        return None

    def cache_summary(self, user_id, summary, last_memory_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO summary_cache (user_id, summary, last_memory_id, timestamp)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, summary, last_memory_id))
        self.conn.commit()

    def close(self):
        self.conn.close()

def main():
    memory_manager = MemoryManager()

    while True:
        command = input("Enter command (add/retrieve/exit): ").lower()

        if command == 'add':
            user_id = input("Enter user ID: ")
            memory = input("Enter memory to add: ")
            memory_id = memory_manager.add_memory(user_id, memory)
            print(f"Memory added with ID: {memory_id}")

        elif command == 'retrieve':
            user_id = input("Enter user ID: ")
            memories = memory_manager.get_memories(user_id)
            print("\nLatest memory:")
            print(memories['latest_memory'])
            print("\nOverall summary:")
            print(memories['overall_summary'])

        elif command == 'exit':
            memory_manager.close()
            print("Goodbye!")
            break

        else:
            print("Invalid command. Please try again.")

if __name__ == "__main__":
    main()