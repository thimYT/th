import os
import sqlite3
import random
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()
DB_NAME = "game.db"

# Создаем папку images, если её еще нет, и подключаем раздачу картинок
os.makedirs("images", exist_ok=True)
app.mount("/images", StaticFiles(directory="images"), name="images")

# В поле "image" можно указывать как локальный файл ("/images/knife.png"),
# так и прямую ссылку из интернета ("https://...")
ITEMS_DB = {
    1: {
        "id": 1,
        "name": "Ржавый нож",
        "price": 50,
        "rarity": "common",
        "image": "/images/item1.png",
        "fallback": "🗡️"
    },
    2: {
        "id": 2,
        "name": "Пистолет Старт",
        "price": 120,
        "rarity": "common",
        "image": "/images/item2.png",
        "fallback": "🔫"
    },
    3: {
        "id": 3,
        "name": "Автомат Вектор",
        "price": 300,
        "rarity": "rare",
        "image": "/images/item3.png",
        "fallback": "🪖"
    },
    4: {
        "id": 4,
        "name": "Снайперка Азимов",
        "price": 750,
        "rarity": "epic",
        "image": "/images/item4.png",
        "fallback": "🎯"
    },
    5: {
        "id": 5,
        "name": "Нож Керамбит",
        "price": 1800,
        "rarity": "legendary",
        "image": "/images/item5.png",
        "fallback": "⚔️"
    },
    6: {
        "id": 6,
        "name": "Золотой Дракон",
        "price": 5000,
        "rarity": "mythic",
        "image": "/images/item6.png",
        "fallback": "🐉"
    },
}

CASES_DB = {
    1: {
        "id": 1,
        "name": "Бомж-кейс",
        "price": 100,
        "image": "/images/case1.png",
        "fallback": "📦",
        "drops": [
            {"item_id": 1, "weight": 60},
            {"item_id": 2, "weight": 30},
            {"item_id": 3, "weight": 10},
        ]
    },
    2: {
        "id": 2,
        "name": "Оружейный ящик",
        "price": 400,
        "image": "/images/case2.png",
        "fallback": "🧰",
        "drops": [
            {"item_id": 2, "weight": 45},
            {"item_id": 3, "weight": 35},
            {"item_id": 4, "weight": 15},
            {"item_id": 5, "weight": 5},
        ]
    },
    3: {
        "id": 3,
        "name": "Элитный сейф",
        "price": 1500,
        "image": "/images/case3.png",
        "fallback": "💎",
        "drops": [
            {"item_id": 3, "weight": 40},
            {"item_id": 4, "weight": 35},
            {"item_id": 5, "weight": 20},
            {"item_id": 6, "weight": 5},
        ]
    }
}

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            balance INTEGER DEFAULT 1000
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            inv_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            item_id INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_or_create_user(user_id: str) -> int:
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (user_id, 1000))
        conn.commit()
        balance = 1000
    else:
        balance = int(row[0])
    conn.close()
    return balance

class OpenCaseReq(BaseModel):
    user_id: str
    case_id: int

class SellItemReq(BaseModel):
    user_id: str
    inv_id: int

class UpgradeReq(BaseModel):
    user_id: str
    inv_ids: List[int]
    coins_bet: int
    target_type: str
    target_item_id: Optional[int] = None
    target_coins: Optional[int] = None

@app.get("/")
def serve_frontend():
    return FileResponse("index.html")

@app.get("/api/state/{user_id}")
def get_state(user_id: str):
    balance = get_or_create_user(user_id)
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT inv_id, item_id FROM inventory WHERE user_id = ? ORDER BY inv_id DESC", (user_id,))
    rows = cur.fetchall()
    conn.close()

    inv_list = []
    for inv_id, item_id in rows:
        if item_id in ITEMS_DB:
            item_info = ITEMS_DB[item_id].copy()
            item_info["inv_id"] = inv_id
            inv_list.append(item_info)

    # Передаем кейсы вместе со списком возможных предметов для анимации рулетки
    cases_with_items = []
    for c in CASES_DB.values():
        c_copy = c.copy()
        c_copy["possible_items"] = [ITEMS_DB[d["item_id"]] for d in c["drops"] if d["item_id"] in ITEMS_DB]
        cases_with_items.append(c_copy)

    return {
        "balance": balance,
        "inventory": inv_list,
        "cases": cases_with_items,
        "all_items": list(ITEMS_DB.values())
    }

@app.post("/api/bonus/{user_id}")
def add_bonus(user_id: str):
    balance = get_or_create_user(user_id)
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + 500 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"balance": balance + 500}

@app.post("/api/open_case")
def open_case(req: OpenCaseReq):
    if req.case_id not in CASES_DB:
        raise HTTPException(status_code=400, detail="Кейс не найден")
    
    case = CASES_DB[req.case_id]
    balance = get_or_create_user(req.user_id)

    if balance < case["price"]:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    population = [d["item_id"] for d in case["drops"]]
    weights = [d["weight"] for d in case["drops"]]
    won_item_id = random.choices(population, weights=weights, k=1)[0]

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (case["price"], req.user_id))
    cur.execute("INSERT INTO inventory (user_id, item_id) VALUES (?, ?)", (req.user_id, won_item_id))
    conn.commit()
    conn.close()

    return {
        "won_item": ITEMS_DB[won_item_id],
        "new_balance": balance - case["price"]
    }

@app.post("/api/sell_item")
def sell_item(req: SellItemReq):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT item_id FROM inventory WHERE inv_id = ? AND user_id = ?", (req.inv_id, req.user_id))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=400, detail="Предмет не найден")

    price = ITEMS_DB[int(row[0])]["price"]
    cur.execute("DELETE FROM inventory WHERE inv_id = ?", (req.inv_id,))
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (price, req.user_id))
    conn.commit()
    conn.close()
    return {"sold_for": price}

@app.post("/api/upgrade")
def do_upgrade(req: UpgradeReq):
    if req.coins_bet < 0:
        raise HTTPException(status_code=400, detail="Некорректная ставка монет")

    balance = get_or_create_user(req.user_id)
    if req.coins_bet > balance:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    items_total_value = 0
    if req.inv_ids:
        placeholders = ",".join("?" for _ in req.inv_ids)
        cur.execute(f"SELECT inv_id, item_id FROM inventory WHERE user_id = ? AND inv_id IN ({placeholders})", [req.user_id] + req.inv_ids)
        found_rows = cur.fetchall()
        if len(found_rows) != len(req.inv_ids):
            conn.close()
            raise HTTPException(status_code=400, detail="Ошибка проверки предметов инвентаря")
        for _, item_id in found_rows:
            items_total_value += ITEMS_DB[item_id]["price"]

    total_bet = items_total_value + req.coins_bet
    if total_bet <= 0:
        conn.close()
        raise HTTPException(status_code=400, detail="Выберите вещи или введите монеты")

    if req.target_type == "item":
        if req.target_item_id not in ITEMS_DB:
            conn.close()
            raise HTTPException(status_code=400, detail="Целевой предмет не найден")
        target_value = ITEMS_DB[req.target_item_id]["price"]
    else:
        if not req.target_coins or req.target_coins <= total_bet:
            conn.close()
            raise HTTPException(status_code=400, detail="Желаемая сумма должна быть больше ставки")
        target_value = req.target_coins

    if target_value <= total_bet:
        conn.close()
        raise HTTPException(status_code=400, detail="Цель должна быть дороже вашей ставки")

    chance = round((total_bet / target_value) * 92, 2)
    chance = max(1.0, min(80.0, chance))

    if req.coins_bet > 0:
        cur.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (req.coins_bet, req.user_id))
    if req.inv_ids:
        placeholders = ",".join("?" for _ in req.inv_ids)
        cur.execute(f"DELETE FROM inventory WHERE inv_id IN ({placeholders})", req.inv_ids)

    roll = random.uniform(0, 100)
    is_win = roll <= chance

    if is_win:
        if req.target_type == "item":
            cur.execute("INSERT INTO inventory (user_id, item_id) VALUES (?, ?)", (req.user_id, req.target_item_id))
        else:
            cur.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (target_value, req.user_id))

    conn.commit()
    conn.close()

    return {
        "win": is_win,
        "chance": chance
    }