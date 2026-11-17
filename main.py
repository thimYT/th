import os
import json
import base64
import random
import urllib.request
import urllib.error
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.getenv("GITHUB_REPO", "").strip()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "").strip()
DB_PATH = "database.json"

ITEMS_DB = {
    1: {"id": 1, "name": "Ржавый нож", "price": 50, "rarity": "common", "image": "/images/item1.png", "fallback": "🗡️"},
    2: {"id": 2, "name": "Пистолет Старт", "price": 120, "rarity": "common", "image": "/images/item2.png", "fallback": "🔫"},
    3: {"id": 3, "name": "Автомат Вектор", "price": 300, "rarity": "rare", "image": "/images/item3.png", "fallback": "🪖"},
    4: {"id": 4, "name": "Снайперка Азимов", "price": 750, "rarity": "epic", "image": "/images/item4.png", "fallback": "🎯"},
    5: {"id": 5, "name": "Нож Керамбит", "price": 1800, "rarity": "legendary", "image": "/images/item5.png", "fallback": "⚔️"},
    6: {"id": 6, "name": "Золотой Дракон", "price": 5000, "rarity": "mythic", "image": "/images/item6.png", "fallback": "🐉"},
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

def send_tg_message(chat_id: str, text: str) -> bool:
    if not BOT_TOKEN or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.status == 200
    except Exception:
        return False

def github_load_db() -> dict:
    default_db = {"users": {}, "next_inv_id": 1}
    if not GITHUB_TOKEN or not GITHUB_REPO:
        if os.path.exists(DB_PATH):
            with open(DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return default_db

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DB_PATH}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "BrainDrop-App"
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = base64.b64decode(data["content"]).decode("utf-8")
            return json.loads(content)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return default_db
        return default_db
    except Exception:
        return default_db

def github_save_db(db: dict):
    if not GITHUB_TOKEN or not GITHUB_REPO:
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
        return

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DB_PATH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "BrainDrop-App"
    }

    sha = None
    try:
        get_req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(get_req, timeout=10) as resp:
            existing = json.loads(resp.read().decode("utf-8"))
            sha = existing.get("sha")
    except Exception:
        pass

    encoded_content = base64.b64encode(
        json.dumps(db, ensure_ascii=False, indent=2).encode("utf-8")
    ).decode("utf-8")

    payload = {
        "message": "Update database.json",
        "content": encoded_content
    }
    if sha:
        payload["sha"] = sha

    put_req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="PUT"
    )
    try:
        with urllib.request.urlopen(put_req, timeout=10):
            pass
    except Exception:
        pass

def get_user(db: dict, user_id: str) -> dict:
    if "users" not in db:
        db["users"] = {}
    if "next_inv_id" not in db:
        db["next_inv_id"] = 1
    if user_id not in db["users"]:
        db["users"][user_id] = {"balance": 1000, "inventory": []}
    return db["users"][user_id]

class TopupReq(BaseModel):
    user_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None

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
    db = github_load_db()
    user = get_user(db, user_id)

    inv_list = []
    for entry in user["inventory"]:
        item_id = entry["item_id"]
        if item_id in ITEMS_DB:
            item_info = ITEMS_DB[item_id].copy()
            item_info["inv_id"] = entry["inv_id"]
            inv_list.append(item_info)

    cases_out = []
    for c in CASES_DB.values():
        c_copy = c.copy()
        c_copy["possible_items"] = [ITEMS_DB[d["item_id"]] for d in c["drops"] if d["item_id"] in ITEMS_DB]
        cases_out.append(c_copy)

    return {
        "balance": user["balance"],
        "inventory": list(reversed(inv_list)),
        "cases": cases_out,
        "all_items": list(ITEMS_DB.values())
    }

@app.post("/api/request_topup")
def request_topup(req: TopupReq):
    if not BOT_TOKEN:
        raise HTTPException(status_code=500, detail="Токен бота не настроен на сервере")

    if req.username:
        user_mention = f"@{req.username.lstrip('@')}"
    elif req.first_name:
        user_mention = f"{req.first_name} (ID: {req.user_id})"
    else:
        user_mention = f"ID: {req.user_id}"

    # 1. Сообщение пользователю в личку бота (работает, если user_id — числовой ID Telegram)
    user_sent = False
    if req.user_id.isdigit():
        user_sent = send_tg_message(
            req.user_id,
            "Для пополнения с вами свяжется первый освободившийся модератор"
        )

    # 2. Сообщение создателю (админу)
    admin_sent = False
    if ADMIN_CHAT_ID:
        admin_sent = send_tg_message(
            ADMIN_CHAT_ID,
            f"Пользователь {user_mention} хочет пополнить баланс. Направьте к нему модератора."
        )

    if not admin_sent and not user_sent:
        raise HTTPException(status_code=400, detail="Не удалось отправить сообщение. Убедитесь, что вы запустили бота (/start)")

    return {"ok": True, "user_sent": user_sent, "admin_sent": admin_sent}

@app.post("/api/open_case")
def open_case(req: OpenCaseReq):
    if req.case_id not in CASES_DB:
        raise HTTPException(status_code=400, detail="Кейс не найден")

    db = github_load_db()
    user = get_user(db, req.user_id)
    case = CASES_DB[req.case_id]

    if user["balance"] < case["price"]:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    population = [d["item_id"] for d in case["drops"]]
    weights = [d["weight"] for d in case["drops"]]
    won_item_id = random.choices(population, weights=weights, k=1)[0]

    user["balance"] -= case["price"]
    inv_id = db["next_inv_id"]
    db["next_inv_id"] += 1
    user["inventory"].append({"inv_id": inv_id, "item_id": won_item_id})

    github_save_db(db)

    return {
        "won_item": ITEMS_DB[won_item_id],
        "new_balance": user["balance"]
    }

@app.post("/api/sell_item")
def sell_item(req: SellItemReq):
    db = github_load_db()
    user = get_user(db, req.user_id)

    found_idx = None
    found_item_id = None
    for idx, entry in enumerate(user["inventory"]):
        if entry["inv_id"] == req.inv_id:
            found_idx = idx
            found_item_id = entry["item_id"]
            break

    if found_idx is None or found_item_id not in ITEMS_DB:
        raise HTTPException(status_code=400, detail="Предмет не найден")

    price = ITEMS_DB[found_item_id]["price"]
    user["inventory"].pop(found_idx)
    user["balance"] += price

    github_save_db(db)
    return {"sold_for": price, "new_balance": user["balance"]}

@app.post("/api/upgrade")
def do_upgrade(req: UpgradeReq):
    if req.coins_bet < 0:
        raise HTTPException(status_code=400, detail="Некорректная ставка монет")

    db = github_load_db()
    user = get_user(db, req.user_id)

    if req.coins_bet > user["balance"]:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    items_total_value = 0
    selected_set = set(req.inv_ids)
    matched_entries = [e for e in user["inventory"] if e["inv_id"] in selected_set]

    if len(matched_entries) != len(selected_set):
        raise HTTPException(status_code=400, detail="Ошибка проверки предметов инвентаря")

    for e in matched_entries:
        items_total_value += ITEMS_DB[e["item_id"]]["price"]

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

    chance = round((total_bet / target_value) * 92, 2)
    chance = max(1.0, min(80.0, chance))

    user["balance"] -= req.coins_bet
    user["inventory"] = [e for e in user["inventory"] if e["inv_id"] not in selected_set]

    roll = random.uniform(0, 100)
    is_win = roll <= chance

    if is_win:
        if req.target_type == "item":
            inv_id = db["next_inv_id"]
            db["next_inv_id"] += 1
            user["inventory"].append({"inv_id": inv_id, "item_id": req.target_item_id})
        else:
            user["balance"] += target_value

    github_save_db(db)

    return {
        "win": is_win,
        "chance": chance
    }