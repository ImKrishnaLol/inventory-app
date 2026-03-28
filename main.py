from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import psycopg2
import uuid

app = FastAPI()

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
# 📊 ITEMS CRUD
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
    item_id = str(uuid.uuid4())
    try:
        cur.execute(
            """
            INSERT INTO items (
                id, name, shop_category, unit, unit_factor,
                irreplacable, current_qty, ideal_qty,
                low_stock_ratio, consumption_rate
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
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
            )
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"message": "Item added", "id": item_id}

@app.put("/update-item/{item_id}")
def update_item(item_id: str, item: Item):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE items
            SET name=%s,
                shop_category=%s,
                unit=%s,
                unit_factor=%s,
                irreplacable=%s,
                current_qty=%s,
                ideal_qty=%s,
                low_stock_ratio=%s,
                consumption_rate=%s,
                last_updated = NOW()
            WHERE id=%s
            """,
            (
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
# 🗂️ GROUPS CRUD
# =========================

@app.get("/groups")
def get_groups():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM groups ORDER BY name")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {
            "id": str(r[0]),
            "name": r[1],
            "irreplacable": r[2],
            "members": r[3]  # UUID[] array
        }
        for r in rows
    ]

@app.post("/groups/add")
def add_group(group: Group):
    conn = get_conn()
    cur = conn.cursor()
    group_id = str(uuid.uuid4())
    try:
        cur.execute(
            "INSERT INTO groups (id, name, irreplacable, members) VALUES (%s, %s, %s, %s)",
            (group_id, group.name, group.irreplacable, [])
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"message": "Group added", "id": group_id}

@app.put("/groups/update-members/{group_id}")
def update_group_members(group_id: str, member: GroupMember):
    conn = get_conn()
    cur = conn.cursor()
    try:
        # Fetch existing members
        cur.execute("SELECT members FROM groups WHERE id=%s", (group_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Group not found")
        members = row[0] if row[0] else []

        # Add item or child group
        if member.item_id:
            if member.item_id not in members:
                members.append(member.item_id)
        if member.child_group_id:
            if member.child_group_id not in members:
                members.append(member.child_group_id)

        # Update array
        cur.execute("UPDATE groups SET members=%s WHERE id=%s", (members, group_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"message": "Group members updated"}
