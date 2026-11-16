import os
import json
import base64
import random
import urllib.request
import urllib.error
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

os.makedirs("images", exist_ok=True)
app.mount("/images", StaticFiles(directory="images"), name="images")

# Настройки GitHub для сохранения базы данных
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.environ.get("GITHUB_REPO", "thimYT/th").strip()
GITHUB_DB_PATH = "database.json"
LOCAL_FALLBACK_FILE = "database.json"

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

# --- РАБОТА С БАЗОЙ ДАННЫХ ЧЕРЕЗ GITHUB API ---
def github_load_db():
    if not GITHUB_TOKEN or not GITHUB_REPO:
        if os.path.exists(LOCAL_FALLBACK_FILE):
            with open(LOCAL_FALLBACK_FILE, "r", encoding="utf-8") as f:
                return json.load(f), None
        return {"users": {}, "next_inv_id": 1}, None

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_DB_PATH}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "FastAPI-Game-Server"
    })
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            sha = payload.get("sha")
            raw_content = base64.b64decode(payload["content"]).decode("utf-8")
            data = json.loads(raw_content)
            return data, sha
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"users": {}, "next_inv_id": 1}, None
        raise
    except Exception:
        return {"users": {}, "next_inv_id": 1}, None

def github_save_db(data, sha=None):
    with open(LOCAL_FALLBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    if not GITHUB_TOKEN or not GITHUB_REPO:
        return

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_DB_PATH}"
    encoded_content = base64.b64encode(
        json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    ).decode("utf-8")

    body = {
        "message": "Update player save data",
        "content": encoded_content
    }
    if sha:
        body["sha"] = sha

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        method="PUT",
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "FastAPI-Game-Server"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        # Если sha устарел из-за параллельного запроса, пробуем перечитать sha и сохранить еще раз
        if e.code in (409, 422):
            _, fresh_sha = github_load_db()
            if fresh_sha:
                body["sha"] = fresh_sha
                retry_req = urllib.request.Request(
                    url,
                    data=json.dumps(body).encode("utf-8"),
                    method="PUT",
                    headers={
                        "Authorization": f"Bearer {GITHUB_TOKEN}",
                        "Accept": "application/vnd.github+json",
                        "Content-Type": "application/json",
                        "User-Agent": "FastAPI-Game-Server"
                    }
                )
                with urllib.request.urlopen(retry_req, timeout=8) as resp2:
                    resp2.read()

def get_user_record(db, user_id: str):
    users = db.setdefault("users", {})
    if user_id not in users:
        users[user_id] = {
            "balance": 1000,
            "inventory": []
        }
        return users[user_id], True
    return users[user_id], False

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
    db, sha = github_load_db()
    user_data, created = get_user_record(db, user_id)
    if created:
        github_save_db(db, sha)

    inv_list = []
    for entry in reversed(user_data.get("inventory", [])):
        item_id = entry.get("item_id")
        if item_id in ITEMS_DB:
            item_info = ITEMS_DB[item_id].copy()
            item_info["inv_id"] = entry["inv_id"]
            inv_list.append(item_info)

    cases_with_items = []
    for c in CASES_DB.values():
        c_copy = c.copy()
        c_copy["possible_items"] = [ITEMS_DB[d["item_id"]] for d in c["drops"] if d["item_id"] in ITEMS_DB]
        cases_with_items.append(c_copy)

    return {
        "balance": user_data["balance"],
        "inventory": inv_list,
        "cases": cases_with_items,
        "all_items": list(ITEMS_DB.values()),
        "github_sync": bool(GITHUB_TOKEN)
    }

@app.post("/api/bonus/{user_id}")
def add_bonus(user_id: str):
    db, sha = github_load_db()
    user_data, _ = get_user_record(db, user_id)
    user_data["balance"] += 500
    github_save_db(db, sha)
    return {"balance": user_data["balance"]}

@app.post("/api/open_case")
def open_case(req: OpenCaseReq):
    if req.case_id not in CASES_DB:
        raise HTTPException(status_code=400, detail="Кейс не найден")

    case = CASES_DB[req.case_id]
    db, sha = github_load_db()
    user_data, _ = get_user_record(db, req.user_id)

    if user_data["balance"] < case["price"]:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    population = [d["item_id"] for d in case["drops"]]
    weights = [d["weight"] for d in case["drops"]]
    won_item_id = random.choices(population, weights=weights, k=1)[0]

    next_id = db.get("next_inv_id", 1)
    db["next_inv_id"] = next_id + 1

    user_data["balance"] -= case["price"]
    user_data["inventory"].append({
        "inv_id": next_id,
        "item_id": won_item_id
    })

    github_save_db(db, sha)

    return {
        "won_item": ITEMS_DB[won_item_id],
        "new_balance": user_data["balance"]
    }

@app.post("/api/sell_item")
def sell_item(req: SellItemReq):
    db, sha = github_load_db()
    user_data, _ = get_user_record(db, req.user_id)

    inv = user_data.get("inventory", [])
    target_entry = next((x for x in inv if x["inv_id"] == req.inv_id), None)
    if not target_entry:
        raise HTTPException(status_code=400, detail="Предмет не найден")

    price = ITEMS_DB[target_entry["item_id"]]["price"]
    user_data["inventory"] = [x for x in inv if x["inv_id"] != req.inv_id]
    user_data["balance"] += price

    github_save_db(db, sha)
    return {"sold_for": price}

@app.post("/api/upgrade")
def do_upgrade(req: UpgradeReq):
    if req.coins_bet < 0:
        raise HTTPException(status_code=400, detail="Некорректная ставка монет")

    db, sha = github_load_db()
    user_data, _ = get_user_record(db, req.user_id)

    if req.coins_bet > user_data["balance"]:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    inv = user_data.get("inventory", [])
    selected_set = set(req.inv_ids)
    found_items = [x for x in inv if x["inv_id"] in selected_set]

    if len(found_items) != len(selected_set):
        raise HTTPException(status_code=400, detail="Ошибка проверки предметов инвентаря")

    items_total_value = sum(ITEMS_DB[x["item_id"]]["price"] for x in found_items)
    total_bet = items_total_value + req.coins_bet

    if total_bet <= 0:
        raise HTTPException(status_code=400, detail="Выберите вещи или введите монеты")

    if req.target_type == "item":
        if req.target_item_id not in ITEMS_DB:
            raise HTTPException(status_code=400, detail="Целевой предмет не найден")
        target_value = ITEMS_DB[req.target_item_id]["price"]
    else:
        if not req.target_coins or req.target_coins <= total_bet:
            raise HTTPException(status_code=400, detail="Желаемая сумма должна быть больше ставки")
        target_value = req.target_coins

    if target_value <= total_bet:
        raise HTTPException(status_code=400, detail="Цель должна быть дороже вашей ставки")

    chance = round((total_bet / target_value) * 92, 2)
    chance = max(1.0, min(80.0, chance))

    # Списываем ставку
    user_data["balance"] -= req.coins_bet
    if selected_set:
        user_data["inventory"] = [x for x in inv if x["inv_id"] not in selected_set]

    roll = random.uniform(0, 100)
    is_win = roll <= chance

    if is_win:
        if req.target_type == "item":
            next_id = db.get("next_inv_id", 1)
            db["next_inv_id"] = next_id + 1
            user_data["inventory"].append({
                "inv_id": next_id,
                "item_id": req.target_item_id
            })
        else:
            user_data["balance"] += target_value

    github_save_db(db, sha)

    return {
        "win": is_win,
        "chance": chance
    }