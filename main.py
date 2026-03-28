from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import psycopg2

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
# 📦 DATA MODEL (UPDATED)
# =========================

class Item(BaseModel):
    name: str
    shop_category: str
    unit: str
    unit_factor: int = Field(gt=0)

    irreplacable: bool = False

    current_qty: int = Field(ge=0)
    ideal_qty: int = Field(ge=0)

    low_stock_ratio: float = Field(ge=0, le=1) = 0.3

    consumption_rate: float | None = Field(default=None, gt=0)

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
            INSERT INTO items (
                name, shop_category, unit, unit_factor,
                irreplacable, current_qty, ideal_qty,
                low_stock_ratio, consumption_rate
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
