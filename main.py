import os
import json
import time
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

if os.path.exists("images"):
    app.mount("/images", StaticFiles(directory="images"), name="images")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.getenv("GITHUB_REPO", "").strip()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "").strip()
DB_FILE_PATH = "database.json"

ITEMS_DB = {
    1: {"id": 1, "name": "Gub", "price": 5, "rarity": "common", "image": "/images/item1.png", "fallback": "🗡️"},
    2: {"id": 2, "name": "Sir Mangus", "price": 7, "rarity": "common", "image": "/images/item2.png", "fallback": "🔫"},
    3: {"id": 3, "name": "Los Mobilis", "price": 9, "rarity": "common", "image": "/images/item3.png", "fallback": "🪖"},
    4: {"id": 4, "name": "La Grande", "price": 12, "rarity": "common", "image": "/images/item4.png", "fallback": "🎯"},
    5: {"id": 5, "name": "Los 67", "price": 14, "rarity": "common", "image": "/images/item5.png", "fallback": "⚔️"},
    6: {"id": 6, "name": "Bacuru", "price": 16, "rarity": "common", "image": "/images/item6.png", "fallback": "🐉"},
    7: {"id": 7, "name": "Bananito", "price": 18, "rarity": "common", "image": "/images/item7.png", "fallback": "🐉"},
    8: {"id": 8, "name": "Money Cat", "price": 19, "rarity": "common", "image": "/images/item8.png", "fallback": "🐉"},
    9: {"id": 9, "name": "Mariachi", "price": 20, "rarity": "rare", "image": "/images/item9.png", "fallback": "🐉"},
    10: {"id": 10, "name": "Nuclearo", "price": 23, "rarity": "rare", "image": "/images/item10.png", "fallback": "🐉"},
    11: {"id": 11, "name": "Gulini", "price": 25, "rarity": "rare", "image": "/images/item11.png", "fallback": "🐉"},
    12: {"id": 12, "name": "Dj Panda", "price": 27, "rarity": "rare", "image": "/images/item12.png", "fallback": "🐉"},
    13: {"id": 13, "name": "Los Candies", "price": 28, "rarity": "rare", "image": "/images/item13.png", "fallback": "🐉"},
    14: {"id": 14, "name": "Mieteteira", "price": 29, "rarity": "rare", "image": "/images/item14.png", "fallback": "🐉"},
    15: {"id": 15, "name": "Money Puggy", "price": 30, "rarity": "rare", "image": "/images/item15.png", "fallback": "🐉"},
    16: {"id": 16, "name": "Noodle Poodle", "price": 31, "rarity": "rare", "image": "/images/item16.png", "fallback": "🐉"},
    17: {"id": 17, "name": "Oni Panda", "price": 32, "rarity": "rare", "image": "/images/item17.png", "fallback": "🐉"},
    18: {"id": 18, "name": "Balloon Baboon", "price": 34, "rarity": "rare", "image": "/images/item18.png", "fallback": "🐉"},
    19: {"id": 19, "name": "Bat-In-The-Box", "price": 35, "rarity": "rare", "image": "/images/item19.png", "fallback": "🐉"},
    20: {"id": 20, "name": "Esok Sekolah", "price": 36, "rarity": "rare", "image": "/images/item20.png", "fallback": "🐉"},
    21: {"id": 21, "name": "Buffalino", "price": 37, "rarity": "rare", "image": "/images/item21.png", "fallback": "🐉"},
    22: {"id": 22, "name": "Honey Bear", "price": 39, "rarity": "rare", "image": "/images/item22.png", "fallback": "🐉"},
    23: {"id": 23, "name": "Tang Tang", "price": 40, "rarity": "epic", "image": "/images/item23.png", "fallback": "🐉"},
    24: {"id": 24, "name": "Coco And Mango", "price": 41, "rarity": "epic", "image": "/images/item24.png", "fallback": "🐉"},
    25: {"id": 25, "name": "Ketupat Kepat", "price": 43, "rarity": "epic", "image": "/images/item25.png", "fallback": "🐉"},
    26: {"id": 26, "name": "La Taco", "price": 44, "rarity": "epic", "image": "/images/item26.png", "fallback": "🐉"},
    27: {"id": 27, "name": "Tic Tac Sahur", "price": 45, "rarity": "epic", "image": "/images/item27.png", "fallback": "🐉"},
    28: {"id": 28, "name": "Los Puggies", "price": 46, "rarity": "epic", "image": "/images/item28.png", "fallback": "🐉"},
    29: {"id": 29, "name": "Orcaledon", "price": 47, "rarity": "epic", "image": "/images/item29.png", "fallback": "🐉"},
    30: {"id": 30, "name": "Ketchuru", "price": 48, "rarity": "epic", "image": "/images/item30.png", "fallback": "🐉"},
    31: {"id": 31, "name": "Los Tangsitos", "price": 49, "rarity": "epic", "image": "/images/item31.png", "fallback": "🐉"},
    32: {"id": 32, "name": "Chicli Chicla", "price": 50, "rarity": "epic", "image": "/images/item32.png", "fallback": "🐉"},
    33: {"id": 33, "name": "Lavadorito", "price": 51, "rarity": "epic", "image": "/images/item33.png", "fallback": "🐉"},
    34: {"id": 34, "name": "Gold Gold Gold", "price": 52, "rarity": "epic", "image": "/images/item34.png", "fallback": "🐉"},
    35: {"id": 35, "name": "Rosetti", "price": 53, "rarity": "epic", "image": "/images/item35.png", "fallback": "🐉"},
    36: {"id": 36, "name": "Garama", "price": 55, "rarity": "legendary", "image": "/images/item36.png", "fallback": "🐉"},
}

CASES_DB = {
    1: {
        "id": 1,
        "name": "Бомжак",
        "price": 10,
        "image": "/images/case1.png",
        "fallback": "📦",
        "drops": [
            {"item_id": 1, "weight": 30},
            {"item_id": 2, "weight": 25},
            {"item_id": 3, "weight": 15},
            {"item_id": 4, "weight": 11.5},
            {"item_id": 5, "weight": 10},
            {"item_id": 6, "weight": 8.5},
        ]
    },
    2: {
        "id": 2,
        "name": "Money$",
        "price": 25,
        "image": "/images/case2.png",
        "fallback": "🧰",
        "drops": [
            {"item_id": 8, "weight": 52.5},
            {"item_id": 15, "weight": 47.5}
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

FREE_CASE_DROPS = [
    {"item_id": 1, "weight": 65},
    {"item_id": 2, "weight": 25},
    {"item_id": 3, "weight": 8},
    {"item_id": 4, "weight": 2},
]
FREE_CASE_COOLDOWN = 12 * 3600

ACTIVE_CRASH_GAMES = {}

def get_default_db():
    return {
        "users": {},
        "next_inv_id": 1,
        "promocodes": {
            "WELCOME500": {"stock": 100, "type": "coins", "amount": 500, "used_by": []},
            "GIFTKNIFE": {"stock": 10, "type": "item", "item_id": 1, "used_by": []}
        }
    }

def github_load_db():
    if not GITHUB_TOKEN or not GITHUB_REPO:
        if os.path.exists(DB_FILE_PATH):
            with open(DB_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data, None
        return get_default_db(), None

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DB_FILE_PATH}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "BrainDrop-App"
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            content = base64.b64decode(res_data["content"]).decode("utf-8")
            db = json.loads(content)
            if "promocodes" not in db:
                db["promocodes"] = get_default_db()["promocodes"]
            return db, res_data["sha"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return get_default_db(), None
        raise HTTPException(status_code=500, detail=f"Ошибка GitHub DB: {e.code}")

def github_save_db(db_data, sha):
    if not GITHUB_TOKEN or not GITHUB_REPO:
        with open(DB_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(db_data, f, ensure_ascii=False, indent=2)
        return

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DB_FILE_PATH}"
    encoded = base64.b64encode(json.dumps(db_data, ensure_ascii=False, indent=2).encode("utf-8")).decode("utf-8")
    payload = {"message": "Update game database", "content": encoded}
    if sha:
        payload["sha"] = sha

    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="PUT", headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "BrainDrop-App"
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()
    except Exception:
        raise HTTPException(status_code=500, detail="Не удалось сохранить данные в GitHub")

def ensure_user(db, user_id: str):
    if user_id not in db["users"]:
        db["users"][user_id] = {
            "balance": 1000,
            "inventory": [],
            "last_free_case": 0
        }
    elif "last_free_case" not in db["users"][user_id]:
        db["users"][user_id]["last_free_case"] = 0
    return db["users"][user_id]

def send_tg_message(chat_id: str, text: str):
    if not BOT_TOKEN or not chat_id:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            resp.read()
    except Exception:
        pass

class OpenCaseReq(BaseModel):
    user_id: str
    case_id: int

class FreeCaseReq(BaseModel):
    user_id: str

class PromoReq(BaseModel):
    user_id: str
    code: str

class SellItemReq(BaseModel):
    user_id: str
    inv_id: int

class TopupReq(BaseModel):
    user_id: str
    username: Optional[str] = ""
    first_name: Optional[str] = ""

class UpgradeReq(BaseModel):
    user_id: str
    inv_ids: List[int]
    coins_bet: float
    target_type: str
    target_item_id: Optional[int] = None
    target_coins: Optional[float] = None

class CrashStartReq(BaseModel):
    user_id: str
    inv_ids: List[int]
    coins_bet: float

class CrashCashoutReq(BaseModel):
    user_id: str
    multiplier: float

@app.get("/")
def serve_frontend():
    return FileResponse("index.html")

@app.get("/api/state/{user_id}")
def get_state(user_id: str):
    db, sha = github_load_db()
    is_new = user_id not in db["users"]
    user = ensure_user(db, user_id)
    if is_new:
        github_save_db(db, sha)

    inv_list = []
    for entry in reversed(user["inventory"]):
        item_id = entry["item_id"]
        if item_id in ITEMS_DB:
            item_info = ITEMS_DB[item_id].copy()
            item_info["inv_id"] = entry["inv_id"]
            inv_list.append(item_info)

    now = int(time.time())
    next_free_at = user.get("last_free_case", 0) + FREE_CASE_COOLDOWN
    free_seconds_left = max(0, next_free_at - now)
    free_case_items = [ITEMS_DB[d["item_id"]] for d in FREE_CASE_DROPS if d["item_id"] in ITEMS_DB]

    return {
        "balance": round(user["balance"], 2),
        "inventory": inv_list,
        "cases": list(CASES_DB.values()),
        "all_items": list(ITEMS_DB.values()),
        "free_seconds_left": free_seconds_left,
        "free_case_items": free_case_items
    }

@app.post("/api/topup_request")
def topup_request(req: TopupReq):
    if not BOT_TOKEN:
        raise HTTPException(status_code=400, detail="Токен бота не настроен на сервере")

    send_tg_message(req.user_id, "Для пополнения с вами свяжется первый освободившийся модератор.")
    user_tag = f"@{req.username}" if req.username else f"{req.first_name} (ID: {req.user_id})"
    if ADMIN_CHAT_ID:
        send_tg_message(ADMIN_CHAT_ID, f"Пользователь {user_tag} хочет пополнить баланс. Направьте к нему модератора.")
    return {"ok": True}

@app.post("/api/open_case")
def open_case(req: OpenCaseReq):
    if req.case_id not in CASES_DB:
        raise HTTPException(status_code=400, detail="Кейс не найден")

    db, sha = github_load_db()
    user = ensure_user(db, req.user_id)
    case = CASES_DB[req.case_id]

    if user["balance"] < case["price"]:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    population = [d["item_id"] for d in case["drops"]]
    weights = [d["weight"] for d in case["drops"]]
    won_item_id = random.choices(population, weights=weights, k=1)[0]

    user["balance"] = round(user["balance"] - case["price"], 2)
    inv_id = db["next_inv_id"]
    db["next_inv_id"] += 1
    user["inventory"].append({"inv_id": inv_id, "item_id": won_item_id})

    github_save_db(db, sha)
    return {"won_item": ITEMS_DB[won_item_id]}

@app.post("/api/open_free_case")
def open_free_case(req: FreeCaseReq):
    db, sha = github_load_db()
    user = ensure_user(db, req.user_id)

    now = int(time.time())
    last_open = user.get("last_free_case", 0)
    if now - last_open < FREE_CASE_COOLDOWN:
        left = FREE_CASE_COOLDOWN - (now - last_open)
        hours = left // 3600
        mins = (left % 3600) // 60
        raise HTTPException(status_code=400, detail=f"Бесплатный кейс будет доступен через {hours}ч {mins}м")

    population = [d["item_id"] for d in FREE_CASE_DROPS]
    weights = [d["weight"] for d in FREE_CASE_DROPS]
    won_item_id = random.choices(population, weights=weights, k=1)[0]

    user["last_free_case"] = now
    inv_id = db["next_inv_id"]
    db["next_inv_id"] += 1
    user["inventory"].append({"inv_id": inv_id, "item_id": won_item_id})

    github_save_db(db, sha)
    return {"won_item": ITEMS_DB[won_item_id]}

@app.post("/api/redeem_promo")
def redeem_promo(req: PromoReq):
    code = req.code.strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Введите промокод")

    db, sha = github_load_db()
    user = ensure_user(db, req.user_id)
    promos = db.get("promocodes", {})

    if code not in promos:
        raise HTTPException(status_code=400, detail="Промокод не найден или недействителен")

    promo = promos[code]
    if promo.get("stock", 0) <= 0:
        raise HTTPException(status_code=400, detail="Активации этого промокода закончились")

    used_by = promo.setdefault("used_by", [])
    if req.user_id in used_by:
        raise HTTPException(status_code=400, detail="Вы уже активировали этот промокод")

    promo_type = promo.get("type", "coins")
    reward_text = ""

    if promo_type == "coins":
        amount = float(promo.get("amount", 0))
        user["balance"] = round(user["balance"] + amount, 2)
        reward_text = f"+{amount} монет"
    elif promo_type == "item":
        item_id = int(promo.get("item_id", 0))
        if item_id not in ITEMS_DB:
            raise HTTPException(status_code=400, detail="Ошибка награды промокода (предмет не найден)")
        inv_id = db["next_inv_id"]
        db["next_inv_id"] += 1
        user["inventory"].append({"inv_id": inv_id, "item_id": item_id})
        reward_text = f"Предмет: {ITEMS_DB[item_id]['name']}"
    else:
        raise HTTPException(status_code=400, detail="Неизвестный тип промокода")

    promo["stock"] -= 1
    used_by.append(req.user_id)

    github_save_db(db, sha)
    return {"message": f"Промокод активирован! Награда: {reward_text}"}

@app.post("/api/sell_item")
def sell_item(req: SellItemReq):
    db, sha = github_load_db()
    user = ensure_user(db, req.user_id)

    target_idx = None
    item_id = None
    for idx, entry in enumerate(user["inventory"]):
        if entry["inv_id"] == req.inv_id:
            target_idx = idx
            item_id = entry["item_id"]
            break

    if target_idx is None or item_id not in ITEMS_DB:
        raise HTTPException(status_code=400, detail="Предмет не найден")

    price = ITEMS_DB[item_id]["price"]
    user["inventory"].pop(target_idx)
    user["balance"] = round(user["balance"] + price, 2)

    github_save_db(db, sha)
    return {"sold_for": price}

@app.post("/api/upgrade")
def do_upgrade(req: UpgradeReq):
    if req.coins_bet < 0:
        raise HTTPException(status_code=400, detail="Некорректная ставка монет")

    db, sha = github_load_db()
    user = ensure_user(db, req.user_id)

    if req.coins_bet > user["balance"]:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    inv_map = {entry["inv_id"]: entry["item_id"] for entry in user["inventory"]}
    items_total_value = 0
    for inv_id in req.inv_ids:
        if inv_id not in inv_map or inv_map[inv_id] not in ITEMS_DB:
            raise HTTPException(status_code=400, detail="Ошибка проверки предметов инвентаря")
        items_total_value += ITEMS_DB[inv_map[inv_id]]["price"]

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

    user["balance"] = round(user["balance"] - req.coins_bet, 2)
    selected_set = set(req.inv_ids)
    user["inventory"] = [e for e in user["inventory"] if e["inv_id"] not in selected_set]

    roll = random.uniform(0, 100)
    is_win = roll <= chance

    if is_win:
        if req.target_type == "item":
            inv_id = db["next_inv_id"]
            db["next_inv_id"] += 1
            user["inventory"].append({"inv_id": inv_id, "item_id": req.target_item_id})
        else:
            user["balance"] = round(user["balance"] + target_value, 2)

    github_save_db(db, sha)
    return {"win": is_win, "chance": chance}

def generate_crash_point():
    r = random.random()
    if r < 0.04:
        return 1.00
    crash = 0.96 / (1.0 - r)
    return round(min(crash, 100.0), 2)

@app.post("/api/crash/start")
def crash_start(req: CrashStartReq):
    if req.coins_bet < 0:
        raise HTTPException(status_code=400, detail="Некорректная ставка монет")

    db, sha = github_load_db()
    user = ensure_user(db, req.user_id)

    if req.coins_bet > user["balance"]:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    inv_map = {entry["inv_id"]: entry["item_id"] for entry in user["inventory"]}
    bet_items = []
    items_total_value = 0

    for inv_id in req.inv_ids:
        if inv_id not in inv_map or inv_map[inv_id] not in ITEMS_DB:
            raise HTTPException(status_code=400, detail="Ошибка проверки предметов инвентаря")
        item_id = inv_map[inv_id]
        items_total_value += ITEMS_DB[item_id]["price"]
        bet_items.append({"inv_id": inv_id, "item_id": item_id})

    total_bet = round(items_total_value + req.coins_bet, 2)
    if total_bet <= 0:
        raise HTTPException(status_code=400, detail="Сделайте ставку монетами или вещами")

    user["balance"] = round(user["balance"] - req.coins_bet, 2)
    selected_set = set(req.inv_ids)
    user["inventory"] = [e for e in user["inventory"] if e["inv_id"] not in selected_set]
    github_save_db(db, sha)

    crash_point = generate_crash_point()
    ACTIVE_CRASH_GAMES[req.user_id] = {
        "crash_point": crash_point,
        "bet_items": bet_items,
        "items_value": items_total_value,
        "coins_bet": req.coins_bet,
        "total_bet": total_bet
    }

    return {"crash_point": crash_point, "total_bet": total_bet}

@app.post("/api/crash/cashout")
def crash_cashout(req: CrashCashoutReq):
    game = ACTIVE_CRASH_GAMES.pop(req.user_id, None)
    if not game:
        raise HTTPException(status_code=400, detail="Активная игра не найдена или ракета уже взорвалась")

    if req.multiplier < 1.0 or req.multiplier > game["crash_point"]:
        raise HTTPException(status_code=400, detail="Ракета уже взорвалась!")

    db, sha = github_load_db()
    user = ensure_user(db, req.user_id)

    total_win_value = round(game["total_bet"] * req.multiplier, 2)
    max_item_price = max(item["price"] for item in ITEMS_DB.values())

    won_item = None
    returned_items = []
    coins_added = 0.0

    if total_win_value > max_item_price:
        for item_entry in game["bet_items"]:
            user["inventory"].append(item_entry)
            returned_items.append(ITEMS_DB[item_entry["item_id"]])

        diff = round(total_win_value - game["items_value"], 2)
        user["balance"] = round(user["balance"] + diff, 2)
        coins_added = diff
    else:
        affordable_items = [item for item in ITEMS_DB.values() if item["price"] <= total_win_value]
        if affordable_items:
            best_item = max(affordable_items, key=lambda x: x["price"])
            inv_id = db["next_inv_id"]
            db["next_inv_id"] += 1
            user["inventory"].append({"inv_id": inv_id, "item_id": best_item["id"]})
            won_item = best_item

            remainder = round(total_win_value - best_item["price"], 2)
            user["balance"] = round(user["balance"] + remainder, 2)
            coins_added = remainder
        else:
            user["balance"] = round(user["balance"] + total_win_value, 2)
            coins_added = total_win_value

    github_save_db(db, sha)
    return {
        "total_win": total_win_value,
        "won_item": won_item,
        "returned_items": returned_items,
        "coins_added": coins_added
    }
