"""
db.py — SQLite persistence layer for Chand & Company AI Marketing Suite.

Two tables:
- products  : saved product catalog (Add / Edit / Delete)
- campaigns : every marketing kit ever generated (history)

init_db() is safe to call every time the app starts. It creates tables if
they don't exist, and adds any new columns to an older campaigns.db without
touching existing rows — so nothing from the original app is ever lost.
"""

import sqlite3
from datetime import datetime

DB_PATH = "campaigns.db"  # unchanged from the original app, so existing data is kept


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT,
            category TEXT,
            tagline TEXT,
            caption TEXT,
            description TEXT,
            image_url TEXT,
            created_at TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            features TEXT,
            price TEXT,
            occasion TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()

    # Lightweight migration: add the new AI-suite columns if this is an
    # older campaigns.db from before the upgrade.
    existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(campaigns)").fetchall()}
    new_columns = {
        "instagram_caption": "TEXT",
        "facebook_caption": "TEXT",
        "whatsapp_caption": "TEXT",
        "hashtags": "TEXT",
    }
    for col, col_type in new_columns.items():
        if col not in existing_cols:
            conn.execute(f"ALTER TABLE campaigns ADD COLUMN {col} {col_type}")
    conn.commit()
    conn.close()


# ---------------------------------------------------------------
# PRODUCTS
# ---------------------------------------------------------------
def add_product(name, category, features, price, occasion):
    conn = get_connection()
    conn.execute(
        "INSERT INTO products (name, category, features, price, occasion, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (name, category, features, price, occasion, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    conn.commit()
    conn.close()


def get_products():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_product(product_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_product(product_id, name, category, features, price, occasion):
    conn = get_connection()
    conn.execute(
        "UPDATE products SET name=?, category=?, features=?, price=?, occasion=? WHERE id=?",
        (name, category, features, price, occasion, product_id),
    )
    conn.commit()
    conn.close()


def delete_product(product_id):
    conn = get_connection()
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------
# CAMPAIGNS
# ---------------------------------------------------------------
def save_campaign(product_name, category, tagline, description, instagram_caption,
                   facebook_caption, whatsapp_caption, hashtags, image_url):
    conn = get_connection()
    conn.execute(
        """INSERT INTO campaigns
           (product_name, category, tagline, caption, description, image_url, created_at,
            instagram_caption, facebook_caption, whatsapp_caption, hashtags)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (product_name, category, tagline, whatsapp_caption, description, image_url,
         datetime.now().strftime("%Y-%m-%d %H:%M"),
         instagram_caption, facebook_caption, whatsapp_caption, hashtags),
    )
    conn.commit()
    conn.close()


def get_campaigns(search_term=None, category_filter=None):
    conn = get_connection()
    query = "SELECT * FROM campaigns WHERE 1=1"
    params = []
    if search_term:
        query += " AND product_name LIKE ?"
        params.append(f"%{search_term}%")
    if category_filter and category_filter != "Sab (All)":
        query += " AND category = ?"
        params.append(category_filter)
    query += " ORDER BY id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_campaign_categories():
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT category FROM campaigns WHERE category IS NOT NULL AND category != ''"
    ).fetchall()
    conn.close()
    return [r["category"] for r in rows]


def delete_campaign(campaign_id):
    conn = get_connection()
    conn.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))
    conn.commit()
    conn.close()


def get_stats():
    conn = get_connection()
    total_products = conn.execute("SELECT COUNT(*) as c FROM products").fetchone()["c"]
    total_campaigns = conn.execute("SELECT COUNT(*) as c FROM campaigns").fetchone()["c"]
    by_category = conn.execute(
        "SELECT category, COUNT(*) as c FROM campaigns WHERE category IS NOT NULL AND category != '' GROUP BY category"
    ).fetchall()
    recent = conn.execute("SELECT product_name, created_at FROM campaigns ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()
    return {
        "total_products": total_products,
        "total_campaigns": total_campaigns,
        "by_category": {r["category"]: r["c"] for r in by_category},
        "recent": [dict(r) for r in recent],
    }