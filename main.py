from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2
import os
from datetime import datetime

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

class Message(BaseModel):
    sender: str  # "A" ili "B"
    text: str
    
@app.post("/messages")
def add_message(msg: Message):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages (sender, text, timestamp) VALUES (%s, %s, %s)",
        (msg.sender, msg.text, datetime.utcnow())
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "ok"}

@app.get("/messages")
def get_messages():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT sender, text, timestamp FROM messages ORDER BY timestamp ASC")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {"sender": r[0], "text": r[1], "timestamp": r[2]}
        for r in rows
    ]



