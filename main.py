import os
import json
import time
import base64
import random
import threading
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
# Список Telegram ID модераторов через запятую, например: "123456,789012"
# Если пусто — заявки уходят только ADMIN_CHAT_ID.
MODERATOR_IDS = [m.strip() for m in os.getenv("MODERATOR_IDS", "").split(",") if m.strip()]
if not MODERATOR_IDS and ADMIN_CHAT_ID:
    MODERATOR_IDS = [ADMIN_CHAT_ID]
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
    37: {"id": 37, "name": "Los Tic-Tacs", "price": 57, "rarity": "legendary", "image": "/images/item37.png", "fallback": "🐉"},
    38: {"id": 38, "name": "Cash Or Card", "price": 60, "rarity": "legendary", "image": "/images/item38.png", "fallback": "🐉"},
    39: {"id": 39, "name": "Ventoliero", "price": 63, "rarity": "legendary", "image": "/images/item39.png", "fallback": "🐉"},
    40: {"id": 40, "name": "Orbi Mochi", "price": 66, "rarity": "legendary", "image": "/images/item40.png", "fallback": "🐉"},
    41: {"id": 41, "name": "Pretzo Robo", "price": 70, "rarity": "mythic", "image": "/images/item41.png", "fallback": "🐉"},
    42: {"id": 42, "name": "Los Spagettis", "price": 75, "rarity": "legendary", "image": "/images/item42.png", "fallback": "🐉"},
    43: {"id": 43, "name": "Cloverat Clapat", "price": 80, "rarity": "legendary", "image": "/images/item43.png", "fallback": "🐉"},
}


CASES_DB = {
    1: {
        "id": 1,
        "name": "Бомжак",
        "category": "regular", # Разные
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
            "category": "regular",
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
            "name": "paslkek",
            "category": "partner",
            "price": 20,
            "partner_id": "1741462977",
            "partner_percent": 10,
            "image": "/images/case3.png",
            "fallback": "💎",
            "drops": [
                {"item_id": 3, "weight": 40},
                {"item_id": 5, "weight": 25},
                {"item_id": 9, "weight": 20},
                {"item_id": 10, "weight": 10},
                {"item_id": 18, "weight": 5},
            ]
        },
    4: {
        "id": 4,
        "name": "Pretzo all-in",
        "category": "all_in",
        "price": 10,
        "image": "/images/case4.png",
        "fallback": "💎",
        "drops": [
            {"item_id": 1, "weight": 99},
            {"item_id": 41, "weight": 1},
        ]
    },
    5: {
        "id": 5,
        "name": "we got buffed",
        "category": "limited",
        "expires_at": 1795629600,
        "price": 68,
        "image": "/images/case5.png",
        "fallback": "⏳",
        "drops": [
            {"item_id": 40, "weight": 52.5},
            {"item_id": 41, "weight": 47.5},
        ]
    },
    6: {
                "id": 6,
                "name": "zahar_99d",
                "category": "partner",
                "price": 20,
                "partner_id": "8450028899",
                "partner_percent": 10,
                "image": "/images/case6.png",
                "fallback": "💎",
                "drops": [
                    {"item_id": 6, "weight": 40},
                    {"item_id": 9, "weight": 25},
                    {"item_id": 14, "weight": 20},
                    {"item_id": 19, "weight": 10},
                    {"item_id": 35, "weight": 5},
                ]
            },
}

FREE_CASE_DROPS = [
    {"item_id": 1, "weight": 65},
    {"item_id": 2, "weight": 25},
    {"item_id": 3, "weight": 8},
    {"item_id": 4, "weight": 2},
]
FREE_CASE_COOLDOWN = 12 * 3600

ACTIVE_CRASH_GAMES = {}
# moder_chat_id -> topup request id, пока модератор вводит сумму пополнения
WAITING_TOPUP_AMOUNT = {}

def get_default_db():
    return {
        "users": {},
        "next_inv_id": 1,
        "next_req_id": 1,
        "withdraw_requests": {},
        "topup_requests": {},
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
                return normalize_db(data), None
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
            return normalize_db(db), res_data["sha"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return get_default_db(), None
        raise HTTPException(status_code=500, detail=f"Ошибка GitHub DB: {e.code}")

def normalize_db(db):
    """Добавляет новые поля в старую базу, чтобы ничего не сломалось."""
    default = get_default_db()
    for key in ("users", "promocodes", "withdraw_requests", "topup_requests"):
        if key not in db:
            db[key] = default[key]
    if "next_inv_id" not in db:
        db["next_inv_id"] = 1
    if "next_req_id" not in db:
        db["next_req_id"] = 1
    return db

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
            "balance": 0,          # ИЗМЕНЕНО: стартовые 1000 монет убраны
            "inventory": [],
            "last_free_case": 0
        }
    elif "last_free_case" not in db["users"][user_id]:
        db["users"][user_id]["last_free_case"] = 0
    return db["users"][user_id]

# ---------- Telegram Bot API ----------

def bot_api(method, payload):
    if not BOT_TOKEN:
        return None
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

def send_tg_message(chat_id: str, text: str):
    if not BOT_TOKEN or not chat_id:
        return
    bot_api("sendMessage", {"chat_id": chat_id, "text": text})

def bot_send_with_keyboard(chat_id: str, text: str, keyboard):
    if not BOT_TOKEN or not chat_id:
        return
    bot_api("sendMessage", {"chat_id": chat_id, "text": text,
                            "reply_markup": {"inline_keyboard": keyboard}})

def notify_moderators(text: str, keyboard=None):
    for m in MODERATOR_IDS:
        if keyboard:
            bot_send_with_keyboard(m, text, keyboard)
        else:
            send_tg_message(m, text)

def answer_cb(cb_id, text=None, alert=False):
    payload = {"callback_query_id": cb_id}
    if text:
        payload["text"] = text
        payload["show_alert"] = alert
    bot_api("answerCallbackQuery", payload)

def mod_name(cb_from):
    return cb_from.get("username") or cb_from.get("first_name") or str(cb_from.get("id"))

def handle_callback(cb):
    cb_id = cb["id"]
    mod_id = str(cb["from"]["id"])
    data = cb.get("data", "") or ""
    if mod_id not in MODERATOR_IDS:
        answer_cb(cb_id, "Вы не модератор.", True)
        return
    parts = data.split(":")
    if len(parts) != 2:
        return
    action, rid = parts[0], parts[1]

    db, sha = github_load_db()
    db = normalize_db(db)

    # ---------- ЗАЯВКИ НА ВЫВОД ----------
    if action in ("wd_take", "wd_done", "wd_fail"):
        reqs = db.setdefault("withdraw_requests", {})
        r = reqs.get(rid)
        if not r:
            answer_cb(cb_id, "Заявка не найдена.", True)
            return
        item = ITEMS_DB.get(r["item_id"], {})
        user = ensure_user(db, r["user_id"])

        if action == "wd_take":
            if r["status"] != "open":
                answer_cb(cb_id, "Заявку уже взял другой модератор.", True)
                return
            r["status"] = "taken"
            r["moderator"] = mod_id
            github_save_db(db, sha)
            name = mod_name(cb["from"])
            answer_cb(cb_id, "Заявка ваша! Свяжитесь с игроком.")
            send_tg_message(r["user_id"],
                f"🤝 Модератор @{name} взял вашу заявку на вывод «{item.get('name', '?')}». Он свяжется с вами для передачи.")
            bot_send_with_keyboard(mod_id,
                f"Вы взяли заявку #{rid} на вывод «{item.get('name', '?')}» ({item.get('price', 0)} 💰) от игрока ID {r['user_id']}.\n"
                f"Свяжитесь с ним и получите предмет. После завершения нажмите кнопку ниже.",
                [[{"text": "✅ Сделка прошла", "callback_data": f"wd_done:{rid}"}],
                 [{"text": "❌ Сделка не прошла", "callback_data": f"wd_fail:{rid}"}]])
            for m in MODERATOR_IDS:
                if m != mod_id:
                    send_tg_message(m, f"Заявка #{rid} на вывод взята модератором @{name}.")
            return

        if action == "wd_done":
            if r["status"] != "taken":
                answer_cb(cb_id, "Заявка не в работе.", True)
                return
            user["inventory"] = [e for e in user["inventory"] if e["inv_id"] != r["inv_id"]]
            r["status"] = "done"
            github_save_db(db, sha)
            answer_cb(cb_id, "Готово! Предмет удалён из инвентаря игрока.")
            send_tg_message(r["user_id"], f"✅ Вывод «{item.get('name', '?')}» завершён. Спасибо, что пользуетесь BrainDrop!")
            return

        if action == "wd_fail":
            if r["status"] != "taken":
                answer_cb(cb_id, "Заявка не в работе.", True)
                return
            for e in user["inventory"]:
                if e["inv_id"] == r["inv_id"]:
                    e["locked"] = False
            r["status"] = "cancelled"
            github_save_db(db, sha)
            answer_cb(cb_id, "Предмет разблокирован, заявка отменена.")
            send_tg_message(r["user_id"], f"❌ Заявка на вывод «{item.get('name', '?')}» отменена. Предмет возвращён в инвентарь.")
            return

    # ---------- ЗАЯВКИ НА ПОПОЛНЕНИЕ ----------
    if action in ("tp_take", "tp_cancel"):
        reqs = db.setdefault("topup_requests", {})
        r = reqs.get(rid)
        if not r:
            answer_cb(cb_id, "Заявка не найдена.", True)
            return

        if action == "tp_take":
            if r["status"] != "open":
                answer_cb(cb_id, "Заявку уже взял другой модератор.", True)
                return
            r["status"] = "taken"
            r["moderator"] = mod_id
            github_save_db(db, sha)
            name = mod_name(cb["from"])
            WAITING_TOPUP_AMOUNT[mod_id] = rid
            answer_cb(cb_id, "Заявка ваша! Теперь отправьте боту сумму пополнения числом.")
            send_tg_message(r["user_id"],
                f"🤝 Модератор @{name} взял вашу заявку на пополнение. Следуйте его инструкциям для перевода.")
            bot_send_with_keyboard(mod_id,
                f"Вы взяли заявку #{rid} на пополнение от игрока ID {r['user_id']}.\n"
                f"1. Свяжитесь с игроком и получите перевод.\n"
                f"2. Отправьте этому боту сумму пополнения ЧИСЛОМ (например: 500) — деньги сразу упадут игроку на баланс.",
                [[{"text": "❌ Отменить заявку", "callback_data": f"tp_cancel:{rid}"}]])
            for m in MODERATOR_IDS:
                if m != mod_id:
                    send_tg_message(m, f"Заявка #{rid} на пополнение взята модератором @{name}.")
            return

        if action == "tp_cancel":
            if r["status"] not in ("open", "taken"):
                answer_cb(cb_id, "Заявка уже закрыта.", True)
                return
            r["status"] = "cancelled"
            github_save_db(db, sha)
            if WAITING_TOPUP_AMOUNT.get(mod_id) == rid:
                WAITING_TOPUP_AMOUNT.pop(mod_id, None)
            answer_cb(cb_id, "Заявка отменена.")
            send_tg_message(r["user_id"], "❌ Ваша заявка на пополнение отменена. Вы можете создать новую.")
            return

def handle_message(msg):
    chat_id = str(msg["chat"]["id"])
    from_id = str(msg["from"]["id"])
    text = (msg.get("text") or "").strip()

    # Модератор вводит сумму пополнения
    if from_id in MODERATOR_IDS and from_id in WAITING_TOPUP_AMOUNT:
        rid = WAITING_TOPUP_AMOUNT[from_id]
        try:
            amount = round(float(text.replace(",", ".")), 2)
            if amount <= 0:
                raise ValueError
        except ValueError:
            send_tg_message(chat_id, "Введите сумму числом, например: 500")
            return
        db, sha = github_load_db()
        db = normalize_db(db)
        r = db.setdefault("topup_requests", {}).get(rid)
        if not r or r["status"] != "taken":
            WAITING_TOPUP_AMOUNT.pop(from_id, None)
            send_tg_message(chat_id, "Эта заявка уже закрыта.")
            return
        user = ensure_user(db, r["user_id"])
        user["balance"] = round(user["balance"] + amount, 2)
        r["status"] = "done"
        r["amount"] = amount
        github_save_db(db, sha)
        WAITING_TOPUP_AMOUNT.pop(from_id, None)
        send_tg_message(chat_id, f"✅ Игроку {r['user_id']} зачислено {amount} монет.")
        send_tg_message(r["user_id"], f"💰 Ваш баланс пополнен на {amount} монет!")
        for m in MODERATOR_IDS:
            if m != from_id:
                send_tg_message(m, f"Заявка #{rid} на пополнение закрыта: +{amount} монет игроку {r['user_id']}.")
        return

    if text.startswith("/start"):
        if from_id in MODERATOR_IDS:
            send_tg_message(chat_id,
                "🛠 Бот BrainDrop для модераторов.\n"
                "• Заявки на вывод/пополнение приходят с кнопками — кто первый нажал, тот ведёт сделку.\n"
                "• По пополнению: после получения перевода отправьте боту сумму числом.")
        else:
            send_tg_message(chat_id, "👋 Это бот проекта BrainDrop. Заявки на пополнение и вывод создаются внутри игры.")

def handle_update(upd):
    if "callback_query" in upd:
        try:
            handle_callback(upd["callback_query"])
        except Exception:
            pass
    elif "message" in upd:
        try:
            handle_message(upd["message"])
        except Exception:
            pass

def bot_loop():
    offset = 0
    while True:
        try:
            data = bot_api("getUpdates", {"offset": offset, "timeout": 30})
            if data and data.get("ok"):
                for upd in data.get("result", []):
                    offset = upd["update_id"] + 1
                    handle_update(upd)
        except Exception:
            time.sleep(2)

if BOT_TOKEN:
    threading.Thread(target=bot_loop, daemon=True).start()

# ---------- Модели запросов ----------

class OpenCaseReq(BaseModel):
    user_id: str
    case_id: int
    count: int = 1

class FreeCaseReq(BaseModel):
    user_id: str

class PromoReq(BaseModel):
    user_id: str
    code: str

class SellItemReq(BaseModel):
    user_id: str
    inv_id: int

class WithdrawReq(BaseModel):
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

class ColorDiceReq(BaseModel):
    user_id: str
    inv_ids: List[int]
    coins_bet: float
    chosen_color: str
    dice_count: int = 4

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
            item_info["locked"] = entry.get("locked", False)
            inv_list.append(item_info)

    now = int(time.time())
    next_free_at = user.get("last_free_case", 0) + FREE_CASE_COOLDOWN
    free_seconds_left = max(0, next_free_at - now)
    free_case_items = [ITEMS_DB[d["item_id"]] for d in FREE_CASE_DROPS if d["item_id"] in ITEMS_DB]

    return {
        "balance": round(user["balance"], 2),
        "inventory": inv_list,
        "cases": [c for c in CASES_DB.values() if not c.get("expires_at") or c["expires_at"] > now],
        "all_items": list(ITEMS_DB.values()),
        "free_seconds_left": free_seconds_left,
        "free_case_items": free_case_items
    }

@app.post("/api/topup_request")
def topup_request(req: TopupReq):
    if not BOT_TOKEN:
        raise HTTPException(status_code=400, detail="Токен бота не настроен на сервере")

    db, sha = github_load_db()
    db = normalize_db(db)
    ensure_user(db, req.user_id)
    reqs = db.setdefault("topup_requests", {})
    for r in reqs.values():
        if r["user_id"] == req.user_id and r["status"] in ("open", "taken"):
            raise HTTPException(status_code=400, detail="У вас уже есть активная заявка на пополнение")

    rid = db.get("next_req_id", 1)
    db["next_req_id"] = rid + 1
    reqs[str(rid)] = {
        "user_id": req.user_id,
        "username": req.username or "",
        "first_name": req.first_name or "",
        "status": "open",
        "moderator": "",
        "amount": None,
        "created_at": int(time.time())
    }
    github_save_db(db, sha)

    user_tag = f"@{req.username}" if req.username else f"{req.first_name or 'игрок'} (ID: {req.user_id})"
    notify_moderators(
        f"💰 Заявка #{rid} на пополнение от {user_tag}.\nКто первый нажмёт — тот ведёт сделку.",
        [[{"text": "🤝 Взять заявку", "callback_data": f"tp_take:{rid}"}]])
    send_tg_message(req.user_id, "💰 Заявка на пополнение создана. Модератор свяжется с вами.")
    return {"ok": True, "req_id": rid}

@app.post("/api/withdraw_request")
def create_withdraw_request(req: WithdrawReq):
    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)

    target = None
    for e in user["inventory"]:
        if e["inv_id"] == req.inv_id:
            target = e
            break
    if not target or target["item_id"] not in ITEMS_DB:
        raise HTTPException(status_code=400, detail="Предмет не найден")
    if target.get("locked"):
        raise HTTPException(status_code=400, detail="Этот предмет уже в заявке на вывод")

    target["locked"] = True
    rid = db.get("next_req_id", 1)
    db["next_req_id"] = rid + 1
    item = ITEMS_DB[target["item_id"]]
    db.setdefault("withdraw_requests", {})[str(rid)] = {
        "user_id": req.user_id,
        "inv_id": req.inv_id,
        "item_id": target["item_id"],
        "status": "open",
        "moderator": "",
        "created_at": int(time.time())
    }
    github_save_db(db, sha)

    notify_moderators(
        f"📤 Заявка #{rid} на вывод «{item['name']}» ({item['price']} 💰) от ID {req.user_id}.\nКто первый нажмёт — тот ведёт сделку.",
        [[{"text": "🤝 Взять заявку", "callback_data": f"wd_take:{rid}"}]])
    send_tg_message(req.user_id,
        f"📤 Заявка на вывод «{item['name']}» создана. Предмет заблокирован до завершения сделки. Модератор скоро свяжется с вами.")
    return {"ok": True, "req_id": rid}

@app.post("/api/open_case")
def open_case(req: OpenCaseReq):
    if req.case_id not in CASES_DB:
        raise HTTPException(status_code=400, detail="Кейс не найден")

    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)
    case = CASES_DB[req.case_id]

    if case.get("expires_at") and int(time.time()) > case["expires_at"]:
        raise HTTPException(status_code=400, detail="Время действия этого кейса истекло")

    count = max(1, min(int(req.count or 1), 10))  # 1x / 3x / 5x
    total_price = round(case["price"] * count, 2)

    if user["balance"] < total_price:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    population = [d["item_id"] for d in case["drops"]]
    weights = [d["weight"] for d in case["drops"]]
    won_ids = random.choices(population, weights=weights, k=count)

    user["balance"] = round(user["balance"] - total_price, 2)

    partner_id = str(case.get("partner_id", "")).strip()
    partner_percent = float(case.get("partner_percent", 0))
    if partner_id and partner_percent > 0 and partner_id != req.user_id:
        partner_user = ensure_user(db, partner_id)
        partner_reward = round(total_price * (partner_percent / 100.0), 2)
        partner_user["balance"] = round(partner_user["balance"] + partner_reward, 2)

    won_inv_ids = []
    for wid in won_ids:
        inv_id = db["next_inv_id"]
        db["next_inv_id"] += 1
        user["inventory"].append({"inv_id": inv_id, "item_id": wid})
        won_inv_ids.append(inv_id)

    github_save_db(db, sha)
    return {"won_items": [ITEMS_DB[i] for i in won_ids], "won_inv_ids": won_inv_ids}

@app.post("/api/open_free_case")
def open_free_case(req: FreeCaseReq):
    db, sha = github_load_db()
    db = normalize_db(db)
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
    return {"won_items": [ITEMS_DB[won_item_id]], "won_inv_ids": [inv_id]}

@app.post("/api/redeem_promo")
def redeem_promo(req: PromoReq):
    code = req.code.strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Введите промокод")

    db, sha = github_load_db()
    db = normalize_db(db)
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
    db = normalize_db(db)
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

    if user["inventory"][target_idx].get("locked"):
        raise HTTPException(status_code=400, detail="Предмет заблокирован заявкой на вывод")

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
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)

    if req.coins_bet > user["balance"]:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    inv_map = {entry["inv_id"]: entry["item_id"] for entry in user["inventory"] if not entry.get("locked")}
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
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)

    if req.coins_bet > user["balance"]:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    inv_map = {entry["inv_id"]: entry["item_id"] for entry in user["inventory"] if not entry.get("locked")}
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
    db = normalize_db(db)
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


DICE_COLORS = ["red", "orange", "yellow", "green", "blue", "purple"]

def get_color_dice_multiplier(dice_count: int, matches: int) -> float:
    if matches <= 0 or matches % 2 == 0:
        return 0.0
    multipliers_table = {
        1: 1.85,
        3: 5.5,
        5: 18.0,
        7: 60.0,
        9: 200.0,
        11: 750.0
    }
    return multipliers_table.get(matches, 1.85)

@app.post("/api/colordice/roll")
def play_color_dice(req: ColorDiceReq):
    color = req.chosen_color.strip().lower()
    if color not in DICE_COLORS:
        raise HTTPException(status_code=400, detail="Выберите один из 6 цветов")
    if req.dice_count < 3 or req.dice_count > 12:
        raise HTTPException(status_code=400, detail="Выберите от 3 до 12 кубиков")
    if req.coins_bet < 0:
        raise HTTPException(status_code=400, detail="Некорректная ставка монет")

    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)

    if req.coins_bet > user["balance"]:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    inv_map = {entry["inv_id"]: entry["item_id"] for entry in user["inventory"] if not entry.get("locked")}
    items_total_value = 0
    for inv_id in req.inv_ids:
        if inv_id not in inv_map or inv_map[inv_id] not in ITEMS_DB:
            raise HTTPException(status_code=400, detail="Ошибка проверки предметов инвентаря")
        items_total_value += ITEMS_DB[inv_map[inv_id]]["price"]

    total_bet = round(items_total_value + req.coins_bet, 2)
    if total_bet <= 0:
        raise HTTPException(status_code=400, detail="Сделайте ставку монетами или вещами")

    user["balance"] = round(user["balance"] - req.coins_bet, 2)
    selected_set = set(req.inv_ids)
    user["inventory"] = [e for e in user["inventory"] if e["inv_id"] not in selected_set]

    rolled_colors = [random.choice(DICE_COLORS) for _ in range(req.dice_count)]
    matches = sum(1 for c in rolled_colors if c == color)
    multiplier = get_color_dice_multiplier(req.dice_count, matches)

    is_win = multiplier > 0
    win_amount = 0.0
    if is_win:
        win_amount = round(total_bet * multiplier, 2)
        user["balance"] = round(user["balance"] + win_amount, 2)

    github_save_db(db, sha)
    return {
        "win": is_win,
        "rolled_colors": rolled_colors,
        "chosen_color": color,
        "matches": matches,
        "dice_count": req.dice_count,
        "multiplier": multiplier,
        "win_amount": win_amount,
        "total_bet": total_bet
    }
