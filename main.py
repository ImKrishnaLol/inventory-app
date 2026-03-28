from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import psycopg2.errors

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
# 📦 DATA MODEL
# =========================

class Item(BaseModel):
    name: str
    category: str
    quantity: int
    threshold: int

# =========================
# 🏠 ROOT
# =========================

@app.get("/")
def home():
    return {"status": "API is running"}

# =========================
# 📊 GET ALL ITEMS
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
            "category": r[2],
            "quantity": r[3],
            "threshold": r[4],
            "last_updated": str(r[5])
        }
        for r in rows
    ]

# =========================
# ➕ ADD ITEM
# =========================

@app.post("/add")
def add_item(item: Item):
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO items (name, category, quantity, threshold)
            VALUES (%s, %s, %s, %s)
            """,
            (item.name, item.category, item.quantity, item.threshold)
        )

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        cur.close()
        conn.close()

    return {"message": "Item added"}

# =========================
# 🔄 UPDATE FULL ITEM
# =========================

@app.put("/update-item/{item_id}")
def update_item(item_id: str, item: Item):
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            UPDATE items
            SET name=%s,
                category=%s,
                quantity=%s,
                threshold=%s,
                last_updated = NOW()
            WHERE id=%s
            """,
            (item.name, item.category, item.quantity, item.threshold, item_id)
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

# =========================
# 🗑️ DELETE ITEM
# =========================

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
