import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="devmate",
    user="devmate_user",
    password="devmate_1234"
)

def init_db():
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id SERIAL PRIMARY KEY,
        conversation_id TEXT,
        question TEXT,
        answer TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    conn.commit()
    cur.close()

def save_chat(conversation_id, question, answer):
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO chats (conversation_id, question, answer) VALUES (%s, %s, %s)",
        (conversation_id, question, answer)
    )

    conn.commit()
    cur.close()
