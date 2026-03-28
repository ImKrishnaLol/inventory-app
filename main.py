from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2

app = FastAPI()

# ✅ Create connection function instead of global connection
def get_conn():
    return psycopg2.connect(
        host="aws-1-ap-southeast-1.pooler.supabase.com",
        database="postgres",
        user="postgres.nqbjmarcjrzfkmtfbqsd",
        password="KG12.,kg120608",
        port="6543"
    )

class Item(BaseModel):
    name: str
    category: str
    quantity: int
    threshold: int

@app.get("/")
def home():
    return {"status": "API is running"}

@app.get("/items")
def get_items():
    # ✅ Create fresh connection per request
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM items")
    rows = cur.fetchall()

    cur.close()
    conn.close()   # ✅ VERY IMPORTANT

    return [
        {
            "id": str(r[0]),
            "name": r[1],
            "category": r[2],
            "quantity": r[3],
            "threshold": r[4],
            "last_updated": str(r[5])
        }
        for r in rows
    ]
