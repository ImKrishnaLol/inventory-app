from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from uuid import uuid4
from psycopg2 import pool
from typing import Optional, List

# =========================
# APP & DB POOL
# =========================
app = FastAPI(title="Inventory + Groups API")

conn_pool = pool.SimpleConnectionPool(
    minconn=1, maxconn=10,
    host="aws-1-ap-southeast-1.pooler.supabase.com",
    database="postgres",
    user="postgres.nqbjmarcjrzfkmtfbqsd",
    password="KG12.,kg120608",
    port="6543"
)

def get_conn(): return conn_pool.getconn()
def release_conn(conn): conn_pool.putconn(conn)

# =========================
# DATA MODELS
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
    consumption_rate: Optional[float] = Field(default=None, gt=0)

class Group(BaseModel):
    id: Optional[str]
    name: str
    irreplacable: bool = False

class GroupMember(BaseModel):
    group_id: str
    item_id: Optional[str] = None
    child_group_id: Optional[str] = None

# =========================
# ROOT
# =========================
@app.get("/")
async def home():
    return {"status": "API is running"}

# =========================
# ITEMS ENDPOINTS
# =========================
@app.get("/items")
async def get_items():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM items ORDER BY name")
    rows = cur.fetchall(); cur.close(); release_conn(conn)
    return [
        dict(
            id=str(r[0]), name=r[1], shop_category=r[2], unit=r[3],
            unit_factor=r[4], irreplacable=r[5], current_qty=r[6],
            ideal_qty=r[7], low_stock_ratio=r[8], consumption_rate=r[9],
            last_updated=str(r[10])
        ) for r in rows
    ]

@app.get("/items-min")
async def get_items_min():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id, name FROM items ORDER BY name")
    rows = cur.fetchall(); cur.close(); release_conn(conn)
    return [{"id": str(r[0]), "name": r[1]} for r in rows]

@app.post("/add-item")
async def add_item(item: Item):
    conn = get_conn(); cur = conn.cursor()
    new_id = str(uuid4())
    try:
        cur.execute("""
            INSERT INTO items (
                id, name, shop_category, unit, unit_factor,
                irreplacable, current_qty, ideal_qty,
                low_stock_ratio, consumption_rate
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            new_id, item.name, item.shop_category, item.unit, item.unit_factor,
            item.irreplacable, item.current_qty, item.ideal_qty,
            item.low_stock_ratio, item.consumption_rate
        ))
        conn.commit()
    except Exception as e:
        conn.rollback(); raise HTTPException(status_code=400, detail=str(e))
    finally: cur.close(); release_conn(conn)
    return {
        "id": new_id, **item.dict(), "last_updated": ""
    }

@app.put("/update-items")
async def update_items(items: List[dict]):
    conn = get_conn(); cur = conn.cursor()
    try:
        for item in items:
            if "id" not in item: continue
            cur.execute("""
                UPDATE items SET
                    name=%s, shop_category=%s, unit=%s, unit_factor=%s,
                    irreplacable=%s, current_qty=%s, ideal_qty=%s,
                    low_stock_ratio=%s, consumption_rate=%s,
                    last_updated=NOW()
                WHERE id=%s
            """, (
                item.get("name"), item.get("shop_category"), item.get("unit"), item.get("unit_factor"),
                item.get("irreplacable"), item.get("current_qty"), item.get("ideal_qty"),
                item.get("low_stock_ratio"), item.get("consumption_rate"), item.get("id")
            ))
        conn.commit()
    except Exception as e:
        conn.rollback(); raise HTTPException(status_code=400, detail=str(e))
    finally: cur.close(); release_conn(conn)
    return {"message": "Items updated"}

@app.delete("/delete-item/{item_id}")
async def delete_item(item_id: str):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM items WHERE id=%s", (item_id,))
        if cur.rowcount==0: raise HTTPException(status_code=404, detail="Item not found")
        conn.commit()
    except Exception as e:
        conn.rollback(); raise HTTPException(status_code=400, detail=str(e))
    finally: cur.close(); release_conn(conn)
    return {"message": "Item deleted"}

# =========================
# GROUPS ENDPOINTS
# =========================
@app.get("/groups")
async def get_groups():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM groups ORDER BY name")
    rows = cur.fetchall(); cur.close(); release_conn(conn)
    return [{"id": str(r[0]), "name": r[1], "irreplacable": r[2]} for r in rows]

@app.get("/groups-min")
async def get_groups_min():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id, name FROM groups ORDER BY name")
    rows = cur.fetchall(); cur.close(); release_conn(conn)
    return [{"id": str(r[0]), "name": r[1]} for r in rows]

@app.post("/add-group")
async def add_group(group: Group):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO groups (id, name, irreplacable) VALUES (%s,%s,%s)",
                    (str(uuid4()), group.name, group.irreplacable))
        conn.commit()
    except Exception as e:
        conn.rollback(); raise HTTPException(status_code=400, detail=str(e))
    finally: cur.close(); release_conn(conn)
    return {"message": "Group added"}

@app.delete("/delete-group/{group_id}")
async def delete_group(group_id: str):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM group_members WHERE group_id=%s", (group_id,))
        cur.execute("DELETE FROM groups WHERE id=%s", (group_id,))
        if cur.rowcount==0: raise HTTPException(status_code=404, detail="Group not found")
        conn.commit()
    except Exception as e:
        conn.rollback(); raise HTTPException(status_code=400, detail=str(e))
    finally: cur.close(); release_conn(conn)
    return {"message": "Group deleted"}

# =========================
# GROUP MEMBERS
# =========================
@app.get("/group-members/{group_id}")
async def get_group_members(group_id: str):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        SELECT gm.id, i.name AS item_name, g2.name AS group_name
        FROM group_members gm
        LEFT JOIN items i ON gm.item_id = i.id
        LEFT JOIN groups g2 ON gm.child_group_id = g2.id
        WHERE gm.group_id=%s
    """, (group_id,))
    rows = cur.fetchall(); cur.close(); release_conn(conn)
    return [{"id": str(r[0]), "item_name": r[1], "group_name": r[2]} for r in rows]

@app.post("/add-member")
async def add_member(member: GroupMember):
    if not member.item_id and not member.child_group_id:
        raise HTTPException(status_code=400, detail="Must provide item_id or child_group_id")
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO group_members (id, group_id, item_id, child_group_id)
            VALUES (%s,%s,%s,%s)
        """, (str(uuid4()), member.group_id, member.item_id, member.child_group_id))
        conn.commit()
    except Exception as e:
        conn.rollback(); raise HTTPException(status_code=400, detail=str(e))
    finally: cur.close(); release_conn(conn)
    return {"message": "Member added"}

@app.delete("/remove-member/{member_id}")
async def remove_member(member_id: str):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM group_members WHERE id=%s", (member_id,))
        if cur.rowcount==0: raise HTTPException(status_code=404, detail="Member not found")
        conn.commit()
    except Exception as e:
        conn.rollback(); raise HTTPException(status_code=400, detail=str(e))
    finally: cur.close(); release_conn(conn)
    return {"message": "Member removed"}
