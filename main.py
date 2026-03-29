from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional
from psycopg2 import pool

# =========================
# APP
# =========================
app = FastAPI(title="Inventory API (Minimal)")

# =========================
# DB CONNECTION POOL
# =========================
conn_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=5,
    host="aws-1-ap-southeast-1.pooler.supabase.com",
    database="postgres",
    user="postgres.nqbjmarcjrzfkmtfbqsd",
    password="KG12.,kg120608",
    port="6543"
)

def get_conn():
    return conn_pool.getconn()

def release_conn(conn):
    conn_pool.putconn(conn)

# =========================
# MODELS (Only definition, no logic yet)
# =========================
class Item(BaseModel):
    id: Optional[str]
    name: str
    shop_category: str
    unit: str
    unit_factor: int = Field(..., gt=0)
    irreplacable: bool = False
    current_qty: int = Field(0, ge=0)
    ideal_qty: int = Field(..., ge=0)
    low_stock_ratio: float = Field(0.3, ge=0, le=1)
    consumption_rate: Optional[float] = Field(default=0.01, gt=0)

class Group(BaseModel):
    id: Optional[str]
    name: str
    irreplacable: bool = False

class GroupMember(BaseModel):
    group_id: str
    item_id: Optional[str] = None
    child_group_id: Optional[str] = None

# =========================
# ROOT (Health Check)
# =========================
@app.get("/")
def home():
    return {"status": "API is running"}

# =========================
# TEST DATABASE CONNECTION
# =========================
@app.get("/test-db")
def test_db():
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT 1;")
        result = cur.fetchone()
        return {"db_status": "connected", "result": result[0]}
    
    finally:
        cur.close()
        release_conn(conn)
