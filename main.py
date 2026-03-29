from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional
from psycopg2 import pool
from uuid import uuid4
from fastapi import HTTPException

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
        
# =========================
# GET ITEMS (READ ONLY)
# =========================
@app.get("/items")
def get_items():
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT 
                id, name, shop_category, unit, unit_factor,
                irreplacable, current_qty, ideal_qty,
                low_stock_ratio, consumption_rate, last_updated
            FROM items
            ORDER BY name
        """)
        rows = cur.fetchall()

        return [
            {
                "id": str(r[0]),
                "name": r[1],
                "shop_category": r[2],
                "unit": r[3],
                "unit_factor": r[4],
                "irreplacable": r[5],
                "current_qty": r[6],
                "ideal_qty": r[7],
                "low_stock_ratio": r[8],
                "consumption_rate": r[9],
                "last_updated": str(r[10]) if r[10] else ""
            }
            for r in rows
        ]

    finally:
        cur.close()
        release_conn(conn)



# =========================
# ADD ITEM
# =========================
@app.post("/items")
def add_item(item: Item):
    conn = get_conn()
    cur = conn.cursor()

    try:
        item_id = str(uuid4())

        cur.execute("""
            INSERT INTO items (
                id, name, shop_category, unit, unit_factor,
                irreplacable, current_qty, ideal_qty,
                low_stock_ratio, consumption_rate
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            item_id,
            item.name,
            item.shop_category,
            item.unit,
            item.unit_factor,
            item.irreplacable,
            item.current_qty,
            item.ideal_qty,
            item.low_stock_ratio,
            item.consumption_rate
        ))

        conn.commit()

        return {
            "id": item_id,
            **item.dict(),
            "last_updated": ""
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# =========================
# DELETE ITEM
# =========================
@app.delete("/items/{item_id}")
def delete_item(item_id: str):
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM items WHERE id = %s", (item_id,))
        
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")

        conn.commit()
        return {"message": "Item deleted"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        cur.close()
        release_conn(conn)
    finally:
        cur.close()
        release_conn(conn)
