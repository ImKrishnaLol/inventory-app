from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from uuid import uuid4
import psycopg2

app = FastAPI(title="Inventory + Groups API")

# =========================
# 🔌 DATABASE CONNECTION
# =========================
def get_conn():
    return psycopg2.connect(
        host="aws-1-ap-southeast-1.pooler.supabase.com",
        database="postgres",
        user="postgres.nqbjmarcjrzfkmtfbqsd",
        password="KG12.,kg120608",
        port="6543"
    )

# =========================
# 📦 DATA MODELS
# =========================
class Item(BaseModel):
    name: str
    shop_category: str
    unit: str
    unit_factor: int = Field(..., gt=0)
    irreplacable: bool = False
    current_qty: int = Field(0, ge=0)
    ideal_qty: int = Field(..., ge=0)
    low_stock_ratio: float = Field(0.3, ge=0, le=1)
    consumption_rate: float | None = Field(default=None, gt=0)

class Group(BaseModel):
    name: str
    irreplacable: bool = False

class GroupMember(BaseModel):
    group_id: str
    item_id: str | None = None
    child_group_id: str | None = None

# =========================
# 🏠 ROOT
# =========================
@app.get("/")
def home():
    return {"status": "API is running"}

# =========================
# 📊 ITEMS ENDPOINTS
# =========================
@app.get("/items")
def get_items():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM items ORDER BY name")
    rows = cur.fetchall()
    cur.close()
    conn.close()
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
            "last_updated": str(r[10])
        }
        for r in rows
    ]

@app.post("/add")
def add_item(item: Item):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO items (
                id, name, shop_category, unit, unit_factor,
                irreplacable, current_qty, ideal_qty,
                low_stock_ratio, consumption_rate
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                str(uuid4()), item.name, item.shop_category, item.unit,
                item.unit_factor, item.irreplacable, item.current_qty,
                item.ideal_qty, item.low_stock_ratio, item.consumption_rate
            )
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"message": "Item added"}

@app.put("/update-item/{item_id}")
def update_item(item_id: str, item: Item):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE items SET
                name=%s, shop_category=%s, unit=%s, unit_factor=%s,
                irreplacable=%s, current_qty=%s, ideal_qty=%s,
                low_stock_ratio=%s, consumption_rate=%s,
                last_updated=NOW()
            WHERE id=%s
            """,
            (
                item.name, item.shop_category, item.unit, item.unit_factor,
                item.irreplacable, item.current_qty, item.ideal_qty,
                item.low_stock_ratio, item.consumption_rate, item_id
            )
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"message": "Item updated"}

@app.delete("/delete-item/{item_id}")
def delete_item(item_id: str):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM items WHERE id=%s", (item_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"message": "Item deleted"}

# =========================
# 📦 GROUPS ENDPOINTS
# =========================
@app.get("/groups")
def get_groups():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM groups ORDER BY name")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": str(r[0]), "name": r[1], "irreplacable": r[2]} for r in rows]

@app.post("/add-group")
def add_group(group: Group):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO groups (id, name, irreplacable) VALUES (%s,%s,%s)",
            (str(uuid4()), group.name, group.irreplacable)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"message": "Group added"}

@app.get("/group-members/{group_id}")
def get_group_members(group_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT gm.id, i.name AS item_name, g2.name AS group_name
        FROM group_members gm
        LEFT JOIN items i ON gm.item_id = i.id
        LEFT JOIN groups g2 ON gm.child_group_id = g2.id
        WHERE gm.group_id=%s
    """, (group_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": str(r[0]), "item_name": r[1], "group_name": r[2]} for r in rows]

@app.post("/add-member")
def add_member(member: GroupMember):
    if not member.item_id and not member.child_group_id:
        raise HTTPException(status_code=400, detail="Must provide item_id or child_group_id")
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO group_members (id, group_id, item_id, child_group_id) VALUES (%s,%s,%s,%s)",
            (str(uuid4()), member.group_id, member.item_id, member.child_group_id)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"message": "Member added"}

@app.delete("/remove-member/{member_id}")
def remove_member(member_id: str):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM group_members WHERE id=%s", (member_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Member not found")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"message": "Member removed"}
