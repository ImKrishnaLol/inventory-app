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
    ideal_qty: int = 0

class GroupMember(BaseModel):
    group_id: str
    item_id: Optional[str] = None
    child_group_id: Optional[str] = None

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    shop_category: Optional[str] = None
    unit: Optional[str] = None
    unit_factor: Optional[int] = None
    irreplacable: Optional[bool] = None
    current_qty: Optional[int] = None
    ideal_qty: Optional[int] = None
    low_stock_ratio: Optional[float] = None
    consumption_rate: Optional[float] = None

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
                "last_updated": r[10].isoformat() if r[10] else None
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
                low_stock_ratio, consumption_rate, last_updated
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
            RETURNING 
                id, name, shop_category, unit, unit_factor,
                irreplacable, current_qty, ideal_qty,
                low_stock_ratio, consumption_rate, last_updated
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

        row = cur.fetchone()
        conn.commit()

        return {
            "id": str(row[0]),
            "name": row[1],
            "shop_category": row[2],
            "unit": row[3],
            "unit_factor": row[4],
            "irreplacable": row[5],
            "current_qty": row[6],
            "ideal_qty": row[7],
            "low_stock_ratio": row[8],
            "consumption_rate": row[9],
            "last_updated": row[10].strftime("%d %b %Y, %H:%M:%S")
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        cur.close()
        release_conn(conn)

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

# =========================
# UPDATE ITEM
# =========================
@app.put("/items/{item_id}")
def update_item(item_id: str, item: Item):
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE items SET
                name=%s,
                shop_category=%s,
                unit=%s,
                unit_factor=%s,
                irreplacable=%s,
                current_qty=%s,
                ideal_qty=%s,
                low_stock_ratio=%s,
                consumption_rate=%s,
                last_updated=NOW()
            WHERE id=%s
            RETURNING last_updated
        """, (
            item.name,
            item.shop_category,
            item.unit,
            item.unit_factor,
            item.irreplacable,
            item.current_qty,
            item.ideal_qty,
            item.low_stock_ratio,
            item.consumption_rate,
            item_id
        ))

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")

        new_time = cur.fetchone()[0]
        conn.commit()

        return {
            "last_updated": new_time.isoformat()
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        cur.close()
        release_conn(conn)

# =========================
# GROUPS
# =========================
@app.get("/groups")
def get_groups():
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("SELECT id, name, irreplacable, ideal_qty FROM groups ORDER BY name")
        rows = cur.fetchall()

        return [
            {
                "id": str(r[0]),
                "name": r[1],
                "irreplacable": r[2],
                "ideal_qty": r[3]
            }
            for r in rows
        ]

    finally:
        cur.close()
        release_conn(conn)

@app.post("/groups")
def add_group(group: Group):
    conn = get_conn()
    cur = conn.cursor()

    try:
        group_id = str(uuid4())

        cur.execute(
            "INSERT INTO groups (id, name, irreplacable, ideal_qty) VALUES (%s,%s,%s,%s)",
            (group_id, group.name, group.irreplacable, group.ideal_qty)
        )

        conn.commit()

        return {"id": group_id, **group.dict()}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        cur.close()
        release_conn(conn)

@app.delete("/groups/{group_id}")
def delete_group(group_id: str):
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM groups WHERE id=%s", (group_id,))

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Group not found")

        conn.commit()
        return {"message": "Group deleted"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        cur.close()
        release_conn(conn)
# =========================
# GET GROUP MEMBERS
# =========================
@app.get("/groups/{group_id}/members")
def get_group_members(group_id: str):
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT 
                gm.id,
                gm.item_id,
                gm.child_group_id,
                i.name,
                g2.name
            FROM group_members gm
            LEFT JOIN items i ON gm.item_id = i.id
            LEFT JOIN groups g2 ON gm.child_group_id = g2.id
            WHERE gm.group_id = %s
        """, (group_id,))

        rows = cur.fetchall()

        return [
            {
                "id": str(r[0]),
                "item_id": str(r[1]) if r[1] else None,
                "child_group_id": str(r[2]) if r[2] else None,
                "item_name": r[3],
                "group_name": r[4]
            }
            for r in rows
        ]

    finally:
        cur.close()
        release_conn(conn)

# =========================
# ADD MEMBER
# =========================
@app.post("/groups/{group_id}/members")
def add_member(group_id: str, member: GroupMember):
    conn = get_conn()
    cur = conn.cursor()

    try:
        if not member.item_id and not member.child_group_id:
            raise HTTPException(status_code=400, detail="Provide item_id or child_group_id")

        cur.execute("""
            INSERT INTO group_members (id, group_id, item_id, child_group_id)
            VALUES (%s, %s, %s, %s)
        """, (
            str(uuid4()),
            group_id,
            member.item_id,
            member.child_group_id
        ))

        conn.commit()
        return {"message": "Member added"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        cur.close()
        release_conn(conn)

# =========================
# DELETE MEMBER
# =========================
@app.delete("/members/{member_id}")
def delete_member(member_id: str):
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM group_members WHERE id=%s", (member_id,))

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Member not found")

        conn.commit()
        return {"message": "Member removed"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        cur.close()
        release_conn(conn)
