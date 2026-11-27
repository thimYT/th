import os
import json
import time
import math
import base64
import random
import threading
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
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
MODERATOR_IDS = [m.strip() for m in os.getenv("MODERATOR_IDS", "").split(",") if m.strip()]
if not MODERATOR_IDS and ADMIN_CHAT_ID:
    MODERATOR_IDS = [ADMIN_CHAT_ID]
DB_FILE_PATH = "database.json"

MINSK_TZ = timezone(timedelta(hours=3))
ONLINE_WINDOW_SEC = 5 * 60
TRADE_COMMISSION = 0.15
TRADE_MAX_ITEMS = 50

def minsk_today_str() -> str:
    return datetime.now(MINSK_TZ).strftime("%Y-%m-%d")

# ---------- ITEMS_DB ----------
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
    44: {"id": 44, "name": "La Ginger Sekolah", "price": 78, "rarity": "legendary", "image": "/images/item44.png", "fallback": "🐉"},
    45: {"id": 45, "name": "Queen Bee", "price": 82, "rarity": "legendary", "image": "/images/item45.png", "fallback": "🐉"},
    46: {"id": 46, "name": "Guest 666", "price": 83, "rarity": "legendary", "image": "/images/item46.png", "fallback": "🐉"},
    47: {"id": 47, "name": "Panda Popanda", "price": 84, "rarity": "legendary", "image": "/images/item47.png", "fallback": "🐉"},
    48: {"id": 48, "name": "Festive 67", "price": 85, "rarity": "legendary", "image": "/images/item48.png", "fallback": "🐉"},
    49: {"id": 49, "name": "Candini Fluffini", "price": 86, "rarity": "legendary", "image": "/images/item49.png", "fallback": "🐉"},
    50: {"id": 50, "name": "Cangurato Gelato", "price": 87, "rarity": "legendary", "image": "/images/item50.png", "fallback": "🐉"},
    51: {"id": 51, "name": "Boppin Bunny", "price": 88, "rarity": "legendary", "image": "/images/item51.png", "fallback": "🐉"},
    52: {"id": 52, "name": "Spooky And Pumpky", "price": 89, "rarity": "legendary", "image": "/images/item52.png", "fallback": "🐉"},
    53: {"id": 53, "name": "Sammyni Fattini", "price": 90, "rarity": "legendary", "image": "/images/item53.png", "fallback": "🐉"},
    54: {"id": 54, "name": "Yetimatic", "price": 91, "rarity": "legendary", "image": "/images/item54.png", "fallback": "🐉"},
    55: {"id": 55, "name": "La Secret", "price": 92, "rarity": "legendary", "image": "/images/item55.png", "fallback": "🐉"},
    56: {"id": 56, "name": "La Food", "price": 94, "rarity": "legendary", "image": "/images/item56.png", "fallback": "🐉"},
    57: {"id": 57, "name": "Los Hackers", "price": 96, "rarity": "legendary", "image": "/images/item57.png", "fallback": "🐉"},
    58: {"id": 58, "name": "Popcuru", "price": 98, "rarity": "legendary", "image": "/images/item58.png", "fallback": "🐉"},
    59: {"id": 59, "name": "Fragrama", "price": 100, "rarity": "legendary", "image": "/images/item59.png", "fallback": "🐉"},
    60: {"id": 60, "name": "Reinito Sleighito", "price": 110, "rarity": "legendary", "image": "/images/item60.png", "fallback": "🐉"},
    61: {"id": 61, "name": "Rico Dinero", "price": 125, "rarity": "legendary", "image": "/images/item61.png", "fallback": "🐉"},
    62: {"id": 62, "name": "Pizza And Ranch", "price": 150, "rarity": "legendary", "image": "/images/item62.png", "fallback": "🐉"},
    63: {"id": 63, "name": "Celestial Pegas", "price": 180, "rarity": "legendary", "image": "/images/item63.png", "fallback": "🐉"},
    64: {"id": 64, "name": "Cooki And Milki", "price": 200, "rarity": "legendary", "image": "/images/item64.png", "fallback": "🐉"},
    65: {"id": 65, "name": "Burguro And Fryuro", "price": 205, "rarity": "legendary", "image": "/images/item65.png", "fallback": "🐉"},
    66: {"id": 66, "name": "Los Chillis", "price": 220, "rarity": "legendary", "image": "/images/item66.png", "fallback": "🐉"},
    67: {"id": 67, "name": "Duggy Bros", "price": 240, "rarity": "legendary", "image": "/images/item67.png", "fallback": "🐉"},
    68: {"id": 68, "name": "Los Admins", "price": 275, "rarity": "legendary", "image": "/images/item68.png", "fallback": "🐉"},
    69: {"id": 69, "name": "Los Sekolahs", "price": 300, "rarity": "legendary", "image": "/images/item69.png", "fallback": "🐉"},
    70: {"id": 70, "name": "Capitano Moby", "price": 325, "rarity": "legendary", "image": "/images/item70.png", "fallback": "🐉"},
    71: {"id": 71, "name": "La Fuse", "price": 345, "rarity": "legendary", "image": "/images/item71.png", "fallback": "🐉"},
    72: {"id": 72, "name": "La Craft", "price": 350, "rarity": "legendary", "image": "/images/item72.png", "fallback": "🐉"},
    73: {"id": 73, "name": "Lavamanta", "price": 360, "rarity": "legendary", "image": "/images/item73.png", "fallback": "🐉"},
    74: {"id": 74, "name": "Cerberus", "price": 375, "rarity": "legendary", "image": "/images/item74.png", "fallback": "🐉"},
    75: {"id": 75, "name": "Sammyni Truckini", "price": 400, "rarity": "legendary", "image": "/images/item75.png", "fallback": "🐉"},
    76: {"id": 76, "name": "Los Amigos", "price": 410, "rarity": "legendary", "image": "/images/item76.png", "fallback": "🐉"},
    77: {"id": 77, "name": "Ginger Gerat", "price": 430, "rarity": "legendary", "image": "/images/item77.png", "fallback": "🐉"},
    78: {"id": 78, "name": "Fortunu", "price": 450, "rarity": "legendary", "image": "/images/item78.png", "fallback": "🐉"},
    79: {"id": 79, "name": "Hopilikalika", "price": 475, "rarity": "legendary", "image": "/images/item79.png", "fallback": "🐉"},
    80: {"id": 80, "name": "Tosto Dino", "price": 480, "rarity": "legendary", "image": "/images/item80.png", "fallback": "🐉"},
    81: {"id": 81, "name": "S'more Serat", "price": 485, "rarity": "legendary", "image": "/images/item81.png", "fallback": "🐉"},
    82: {"id": 82, "name": "Pancake And Syrup", "price": 490, "rarity": "legendary", "image": "/images/item82.png", "fallback": "🐉"},
    83: {"id": 83, "name": "Foxini", "price": 495, "rarity": "legendary", "image": "/images/item83.png", "fallback": "🐉"},
    84: {"id": 84, "name": "La Casa Boo", "price": 497.5, "rarity": "legendary", "image": "/images/item84.png", "fallback": "🐉"},
    85: {"id": 85, "name": "Flying Dutchman", "price": 500, "rarity": "legendary", "image": "/images/item85.png", "fallback": "🐉"},
}

MUTABLE_RARITIES = {"legendary", "mythic"}

MUTATIONS = {
    "normal":  {"name": "Default",  "mult": 1.00, "icon": "/images/mutation.png", "weight": 100},
    "gold":    {"name": "Gold",  "mult": 1.25, "icon": "/images/mutation1.png", "weight": 0},
    "diamond": {"name": "Diamond", "mult": 1.5, "icon": "/images/mutation2.png", "weight": 0},
    "bloodroot": {"name": "Bloodroot", "mult": 2, "icon": "/images/mutation3.png", "weight": 0},
    "candy": {"name": "Candy",   "mult": 4, "icon": "/images/mutation4.png", "weight": 0},
    "lava": {"name": "Lava",   "mult": 6, "icon": "/images/mutation5.png", "weight": 0},
    "galaxy": {"name": "Galaxy",   "mult": 7, "icon": "/images/mutation6.png", "weight": 0},
    "ying yang": {"name": "Ying Yang",   "mult": 7.5, "icon": "/images/mutation7.png", "weight": 0},
    "radioactive": {"name": "Radioactive",   "mult": 8.5, "icon": "/images/mutation8.png", "weight": 0},
    "cursed": {"name": "Cursed",   "mult": 9, "icon": "/images/mutation9.png", "weight": 0},
    "Divine": {"name": "Divine",   "mult": 10, "icon": "/images/mutation10.png", "weight": 0},
    "rainbow": {"name": "Rainbow",   "mult": 10, "icon": "/images/mutation11.png", "weight": 0},
    "cyber": {"name": "Cyber",   "mult": 11, "icon": "/images/mutation12.png", "weight": 0},
    "phantom": {"name": "Phantom",   "mult": 12, "icon": "/images/mutation13.png", "weight": 0},
    "crystal": {"name": "Crystal",   "mult": 13, "icon": "/images/mutation14.png", "weight": 0},
    "eclipse": {"name": "Eclipse",   "mult": 13.5, "icon": "/images/mutation15.png", "weight": 0},
    "hacker": {"name": "Hacker",   "mult": 14, "icon": "/images/mutation16.png", "weight": 0},
}
MUTATION_KEYS = list(MUTATIONS.keys())
MUTATION_WEIGHTS = [MUTATIONS[k]["weight"] for k in MUTATION_KEYS]


def rarity_allows_mutation(rarity: str) -> bool:
    return (rarity or "").lower() in MUTABLE_RARITIES


def roll_mutation(rarity: str) -> str:
    if not rarity_allows_mutation(rarity):
        return "normal"
    return random.choices(MUTATION_KEYS, weights=MUTATION_WEIGHTS, k=1)[0]


def mutation_mult(mutation: str) -> float:
    return float(MUTATIONS.get(mutation, MUTATIONS["normal"])["mult"])


def mutation_icon(mutation: str) -> str:
    return MUTATIONS.get(mutation, MUTATIONS["normal"])["icon"]


def item_with_mutation(item_id: int, mutation: str) -> dict:
    base = ITEMS_DB[item_id]
    mut = mutation if (mutation in MUTATIONS and rarity_allows_mutation(base["rarity"])) else "normal"
    mult = mutation_mult(mut)
    out = dict(base)
    out["base_price"] = base["price"]
    out["mutation"] = mut
    out["mutation_mult"] = mult
    out["mutation_icon"] = mutation_icon(mut)
    out["price"] = round(base["price"] * mult, 2)
    return out


TRAITS_DB = {
     "taco":   {"key": "taco",   "name": "Taco",   "icon": "/images/trait1.png", "percent": -5},
      "crab":   {"key": "crab",   "name": "Crab",   "icon": "/images/trait2.png", "percent": -5},
       "Sombrero":   {"key": "Sombrero",   "name": "Sombrero",   "icon": "/images/trait3.png", "percent": +5},
        "spider":   {"key": "spider",   "name": "Spider",   "icon": "/images/trait4.png", "percent": +3.5}

}
TRAIT_KEYS = list(TRAITS_DB.keys())
# ---------- ПАДАЮЩАЯ КИРКА ----------
PICKAXES = {
    "wooden":  {"name": "wooden", "hp": 100, "damage": 1, "cost": 50,   "icon": "/images/pick_wood.png",    "fallback": "⛏️"},
    "stone":   {"name": "stone",   "hp": 150, "damage": 2, "cost": 150,  "icon": "/images/pick_stone.png",   "fallback": "⛏️"},
    "iron":    {"name": "iron",   "hp": 200, "damage": 3, "cost": 400,  "icon": "/images/pick_iron.png",    "fallback": "⛏️"},
    "diamond": {"name": "diamond",   "hp": 300, "damage": 5, "cost": 1000, "icon": "/images/pick_diamond.png", "fallback": "⛏️"},
}

ORES = {
    "coal":    {"name": "coal",    "value": 1,  "weight": 40, "icon": "/images/ore_coal.png",    "fallback": "⚫"},
    "copper":  {"name": "copper",     "value": 3,  "weight": 25, "icon": "/images/ore_copper.png",  "fallback": "🟠"},
    "iron":    {"name": "iron",   "value": 6,  "weight": 15, "icon": "/images/ore_iron.png",    "fallback": "⚙️"},
    "gold":    {"name": "gold",   "value": 12, "weight": 10, "icon": "/images/ore_gold.png",    "fallback": "🟡"},
    "diamond": {"name": "diamond",    "value": 25, "weight": 7,  "icon": "/images/ore_diamond.png", "fallback": "💎"},
    "emerald": {"name": "emerald",  "value": 50, "weight": 3,  "icon": "/images/ore_emerald.png", "fallback": "🟢"},
}

SPECIAL_CELLS = {
    "tnt":       {"name": "TNT",      "weight": 6,  "icon": "/images/tnt.png",       "fallback": "🧨"},
    "workbench": {"name": "workbench",  "weight": 4,  "icon": "/images/workbench.png", "fallback": "🛠️"},
    "arrow":     {"name": "arrow",  "weight": 4,  "icon": "/images/arrow.png",     "fallback": "⬆️"},
}

PICKAXE_ORE_POOL = [k for k in ORES.keys()]
PICKAXE_ORE_WEIGHTS = [ORES[k]["weight"] for k in PICKAXE_ORE_POOL]

PICKAXE_SPECIAL_POOL = [k for k in SPECIAL_CELLS.keys()]
PICKAXE_SPECIAL_WEIGHTS = [SPECIAL_CELLS[k]["weight"] for k in PICKAXE_SPECIAL_POOL]

PICKAXE_MAX_DEPTH = 60  # максимум блоков, которые может пройти кирка


def pickaxe_roll_cell() -> dict:
    """Возвращает один блок шахты: пустой, руда или спец-клетка."""
    r = random.random()
    total_special = sum(PICKAXE_SPECIAL_WEIGHTS)
    # 10% на спец-клетку
    if r < 0.10:
        sp = random.choices(PICKAXE_SPECIAL_POOL, weights=PICKAXE_SPECIAL_WEIGHTS, k=1)[0]
        return {"type": "special", "key": sp}
    # 40% пустой блок
    if r < 0.50:
        return {"type": "empty"}
    # остальное — руда
    ore = random.choices(PICKAXE_ORE_POOL, weights=PICKAXE_ORE_WEIGHTS, k=1)[0]
    return {"type": "ore", "key": ore}


def trait_percent_sum(trait_keys: list) -> float:
    total = 0.0
    for k in trait_keys or []:
        if k in TRAITS_DB:
            total += float(TRAITS_DB[k]["percent"])
    return total


def item_with_traits(item_id: int, mutation: str, trait_keys: list) -> dict:
    info = item_with_mutation(item_id, mutation)
    valid = [k for k in (trait_keys or []) if k in TRAITS_DB]
    pct = trait_percent_sum(valid)
    info["traits"] = [
        {"key": k, "name": TRAITS_DB[k]["name"], "icon": TRAITS_DB[k]["icon"], "percent": TRAITS_DB[k]["percent"]}
        for k in valid
    ]
    info["traits_percent"] = pct
    info["price"] = round(info["price"] * (1 + pct / 100.0), 2)
    return info


CASES_DB = {
    1: {"id": 1, "name": "Бомжак", "category": "regular", "price": 10, "image": "/images/case1.png", "fallback": "📦",
        "drops": [{"item_id": 1, "weight": 30}, {"item_id": 2, "weight": 25}, {"item_id": 3, "weight": 15},
                  {"item_id": 4, "weight": 11.5}, {"item_id": 5, "weight": 10}, {"item_id": 6, "weight": 8.5}]},
    2: {"id": 2, "name": "Money$", "category": "regular", "price": 25, "image": "/images/case2.png", "fallback": "🧰",
        "drops": [{"item_id": 8, "weight": 52.5}, {"item_id": 15, "weight": 47.5}]},
    3: {"id": 3, "name": "paslkek", "category": "partner", "price": 20, "partner_id": "1741462977",
        "partner_percent": 10, "image": "/images/case3.png", "fallback": "💎",
        "drops": [{"item_id": 3, "weight": 40}, {"item_id": 5, "weight": 25}, {"item_id": 9, "weight": 20},
                  {"item_id": 10, "weight": 10}, {"item_id": 18, "weight": 5}]},
    4: {"id": 4, "name": "Pretzo all-in", "category": "all_in", "price": 10, "image": "/images/case4.png", "fallback": "💎",
        "drops": [{"item_id": 1, "weight": 99}, {"item_id": 41, "weight": 1}]},
    5: {"id": 5, "name": "we got buffed", "category": "limited", "expires_at": 1795629600, "price": 68,
        "image": "/images/case5.png", "fallback": "⏳",
        "drops": [{"item_id": 40, "weight": 52.5}, {"item_id": 41, "weight": 47.5}]},
    6: {"id": 6, "name": "zahar_99d", "category": "partner", "price": 31, "partner_id": "8450028899",
        "partner_percent": 10, "image": "/images/case6.png", "fallback": "💎",
        "drops": [{"item_id": 6, "weight": 40}, {"item_id": 9, "weight": 25}, {"item_id": 14, "weight": 20},
                  {"item_id": 19, "weight": 10}, {"item_id": 35, "weight": 5}]},
    7: {"id": 7, "name": "Garama", "category": "regular", "price": 100, "image": "/images/case7.png", "fallback": "💎",
        "drops": [{"item_id": 25, "weight": 30}, {"item_id": 35, "weight": 30}, {"item_id": 36, "weight": 27.5},
                  {"item_id": 53, "weight": 7.5}, {"item_id": 70, "weight": 5}]},
}

FREE_CASE_DROPS = [
    {"item_id": 1, "weight": 65},
    {"item_id": 2, "weight": 25},
    {"item_id": 3, "weight": 8},
    {"item_id": 4, "weight": 2},
]
FREE_CASE_COOLDOWN = 12 * 3600

DAILY_BONUS_ITEM_IDS = list(range(9, 24))
DAILY_BONUS_COOLDOWN = 24 * 3600
DAILY_BONUS_REQUIRED_TAG = "braindropdropbot"

ACTIVE_CRASH_GAMES = {}
ACTIVE_MINES_GAMES = {}
ACTIVE_TOWER_GAMES = {}
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
        },
        "daily_drops": {"date": "", "items": []},
        "global_message": {"text": "", "until": 0},
        "events": {},
        "luck_event": {"multiplier": 0, "until": 0},
        "trades": [],
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
    default = get_default_db()
    for key in ("users", "promocodes", "withdraw_requests", "topup_requests"):
        if key not in db:
            db[key] = default[key]
    if "next_inv_id" not in db:
        db["next_inv_id"] = 1
    if "next_req_id" not in db:
        db["next_req_id"] = 1
    if "daily_drops" not in db or not isinstance(db["daily_drops"], dict):
        db["daily_drops"] = {"date": "", "items": []}
    db["daily_drops"].setdefault("date", "")
    db["daily_drops"].setdefault("items", [])
    if "global_message" not in db or not isinstance(db["global_message"], dict):
        db["global_message"] = {"text": "", "until": 0}
    db["global_message"].setdefault("text", "")
    db["global_message"].setdefault("until", 0)
    if "events" not in db or not isinstance(db["events"], dict):
        db["events"] = {}
    if "luck_event" not in db or not isinstance(db["luck_event"], dict):
        db["luck_event"] = {"multiplier": 0, "until": 0}
    db["luck_event"].setdefault("multiplier", 0)
    db["luck_event"].setdefault("until", 0)
    if "trades" not in db or not isinstance(db["trades"], list):
        db["trades"] = []
    for uid, u in db.get("users", {}).items():
        u.setdefault("balance", 0)
        u.setdefault("inventory", [])
        u.setdefault("last_free_case", 0)
        u.setdefault("last_daily_bonus", 0)
        u.setdefault("username", "")
        u.setdefault("first_name", "")
        u.setdefault("photo_url", "")
        u.setdefault("last_seen", 0)
        for entry in u.get("inventory", []):
            entry.setdefault("mutation", "normal")
            entry.setdefault("traits", [])
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
            "balance": 0,
            "inventory": [],
            "last_free_case": 0,
            "last_daily_bonus": 0,
            "username": "",
            "first_name": "",
            "photo_url": "",
            "last_seen": 0,
        }
    else:
        u = db["users"][user_id]
        u.setdefault("balance", 0)
        u.setdefault("inventory", [])
        u.setdefault("last_free_case", 0)
        u.setdefault("last_daily_bonus", 0)
        u.setdefault("username", "")
        u.setdefault("first_name", "")
        u.setdefault("photo_url", "")
        u.setdefault("last_seen", 0)
    return db["users"][user_id]


def touch_user(db, user_id: str):
    u = ensure_user(db, user_id)
    u["last_seen"] = int(time.time())
    return u


def is_online(user) -> bool:
    return int(time.time()) - int(user.get("last_seen", 0)) <= ONLINE_WINDOW_SEC


# ---------- Дроп дня ----------
def record_daily_drop(db, user_id: str, items: List[dict], source: str):
    try:
        today = minsk_today_str()
    except Exception:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dd = db.setdefault("daily_drops", {"date": "", "items": []})
    if dd.get("date") != today:
        dd["date"] = today
        dd["items"] = []
    u = db.get("users", {}).get(user_id, {})
    for it in items or []:
        if not it:
            continue
        entry = {
            "ts": int(time.time()),
            "user_id": str(user_id),
            "username": (u.get("username") or "")[:64],
            "first_name": (u.get("first_name") or "")[:128],
            "photo_url": (u.get("photo_url") or "")[:512],
            "source": source,
            "item_id": int(it.get("id", 0)),
            "name": it.get("name", "?"),
            "rarity": it.get("rarity", "common"),
            "image": it.get("image", ""),
            "fallback": it.get("fallback", "❔"),
            "mutation": it.get("mutation", "normal"),
            "mutation_icon": it.get("mutation_icon", ""),
            "mutation_mult": it.get("mutation_mult", 1.0),
            "price": it.get("price", 0),
        }
        dd["items"].append(entry)
    if len(dd["items"]) > 300:
        dd["items"] = dd["items"][-300:]
    return dd


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

    if from_id in MODERATOR_IDS and from_id in WAITING_TOPUP_AMOUNT:
        rid = WAITING_TOPUP_AMOUNT[from_id]
        try:
            amount = round(float(text.replace(",", ".")), 2)
            if amount <= 0 or amount > 1_000_000:
                raise ValueError
        except ValueError:
            send_tg_message(chat_id, "Введите сумму числом от 0 до 1 000 000, например: 500")
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


# ---------- Модели ----------
class LimboReq(BaseModel):
    user_id: str
    inv_ids: List[int]
    coins_bet: float
    target_multiplier: float

class WheelReq(BaseModel):
    user_id: str
    inv_ids: List[int]
    coins_bet: float
    risk: str = "medium"   # low | medium | high

class KenoReq(BaseModel):
    user_id: str
    inv_ids: List[int]
    coins_bet: float
    picked: List[int]      # номера 1..80
class FuseReq(BaseModel):
    user_id: str
    inv_ids: List[int]      # ровно 4 inv_id   
class PickaxeDropReq(BaseModel):
    user_id: str
    pickaxe_tier: str = "wooden"   # wooden | stone | iron | diamond
    coins_bet: float = 0
    inv_ids: List[int] = []
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
    target_mutation: Optional[str] = "normal"
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

class ProfileSyncReq(BaseModel):
    user_id: str
    username: Optional[str] = ""
    first_name: Optional[str] = ""
    photo_url: Optional[str] = ""

class DailyBonusReq(BaseModel):
    user_id: str

class MinesStartReq(BaseModel):
    user_id: str
    inv_ids: List[int]
    coins_bet: float
    mines: int

class MinesOpenReq(BaseModel):
    user_id: str
    cell: int

class MinesCashoutReq(BaseModel):
    user_id: str

class AdminGlobalMessageReq(BaseModel):
    admin_id: str
    text: str
    duration_seconds: int = 60

class PlinkoPlayReq(BaseModel):
    user_id: str
    inv_ids: List[int]
    coins_bet: float

class TowerStartReq(BaseModel):
    user_id: str
    inv_ids: List[int]
    coins_bet: float

class TowerOpenReq(BaseModel):
    user_id: str
    cell: int

class TowerCashoutReq(BaseModel):
    user_id: str

class AdminUserIdReq(BaseModel):
    admin_id: str

class AdminPromoCreateReq(BaseModel):
    admin_id: str
    code: str
    type: str
    amount: Optional[float] = 0
    item_id: Optional[int] = None
    stock: int = 1

class AdminPromoDeleteReq(BaseModel):
    admin_id: str
    code: str

class AdminBalanceReq(BaseModel):
    admin_id: str
    target_user_id: str
    amount: float
    action: str

class AdminGiveItemReq(BaseModel):
    admin_id: str
    target_user_id: str
    item_id: int
    mutation: Optional[str] = "normal"
    traits: Optional[List[str]] = []

class AdminEventStartReq(BaseModel):
    admin_id: str
    event_type: str
    trait_key: Optional[str] = None
    mutation_key: Optional[str] = None
    tick_seconds: int = 45
    chance_percent: float = 5.0
    duration_seconds: int = 600

class AdminEventStopReq(BaseModel):
    admin_id: str
    event_id: str

class AdminLuckStartReq(BaseModel):
    admin_id: str
    multiplier: int
    duration_seconds: int = 600

class AdminLuckStopReq(BaseModel):
    admin_id: str

# === ЭТАП 6: ТРЕЙДЫ ===
class TradeSendReq(BaseModel):
    from_user_id: str
    target: str          # @username или user_id
    inv_ids: List[int] = []
    coins: float = 0


@app.get("/")
def serve_frontend():
    return FileResponse("index.html")


def _public_daily_drops(db) -> dict:
    dd = db.get("daily_drops", {"date": "", "items": []})
    today = minsk_today_str()
    if dd.get("date") != today:
        return {"date": today, "items": []}
    items = dd.get("items", [])
    return {"date": dd.get("date", today), "items": items}


def _is_admin(user_id: str) -> bool:
    return str(user_id) in [str(m) for m in MODERATOR_IDS]


def _luck_multiplier(db) -> int:
    le = db.get("luck_event", {"multiplier": 0, "until": 0})
    if int(le.get("until", 0)) > int(time.time()):
        return int(le.get("multiplier", 0))
    return 0


def _active_events_public(db) -> list:
    now = int(time.time())
    out = []
    for eid, ev in (db.get("events") or {}).items():
        if int(ev.get("until", 0)) > now:
            out.append({
                "event_id": eid,
                "event_type": ev.get("event_type"),
                "trait_key": ev.get("trait_key"),
                "mutation_key": ev.get("mutation_key"),
                "tick_seconds": ev.get("tick_seconds"),
                "chance_percent": ev.get("chance_percent"),
                "until": ev.get("until"),
            })
    return out


def _active_luck_public(db) -> dict:
    le = db.get("luck_event", {"multiplier": 0, "until": 0})
    if int(le.get("until", 0)) > int(time.time()):
        return {"multiplier": int(le.get("multiplier", 0)), "until": int(le.get("until", 0))}
    return {"multiplier": 0, "until": 0}


@app.get("/api/state/{user_id}")
def get_state(user_id: str):
    db, sha = github_load_db()
    is_new = user_id not in db["users"]
    user = ensure_user(db, user_id)
    if is_new:
        github_save_db(db, sha)
    # online-трекинг
    user["last_seen"] = int(time.time())
    github_save_db(db, sha)

    inv_list = []
    for entry in reversed(user["inventory"]):
        item_id = entry["item_id"]
        if item_id in ITEMS_DB:
            info = item_with_traits(item_id, entry.get("mutation", "normal"), entry.get("traits", []))
            info["inv_id"] = entry["inv_id"]
            info["locked"] = entry.get("locked", False)
            inv_list.append(info)

    now = int(time.time())
    next_free_at = user.get("last_free_case", 0) + FREE_CASE_COOLDOWN
    free_seconds_left = max(0, next_free_at - now)

    next_daily_at = user.get("last_daily_bonus", 0) + DAILY_BONUS_COOLDOWN
    daily_seconds_left = max(0, next_daily_at - now)

    free_case_items = [item_with_traits(d["item_id"], "normal", []) for d in FREE_CASE_DROPS if d["item_id"] in ITEMS_DB]
    daily_bonus_items = [item_with_traits(i, "normal", []) for i in DAILY_BONUS_ITEM_IDS if i in ITEMS_DB]
    all_items = [item_with_traits(i, "normal", []) for i in ITEMS_DB.keys()]
    inv_value = round(sum(e["price"] for e in inv_list), 2)

    gm = db.get("global_message", {"text": "", "until": 0})
    gm_public = {"text": gm.get("text", ""), "until": int(gm.get("until", 0))} if gm.get("text") and int(gm.get("until", 0)) > now else {"text": "", "until": 0}

    return {
        "balance": round(user["balance"], 2),
        "inventory": inv_list,
        "cases": [c for c in CASES_DB.values() if not c.get("expires_at") or c["expires_at"] > now],
        "all_items": all_items,
        "mutations": [
            {"key": k, "name": MUTATIONS[k]["name"], "mult": MUTATIONS[k]["mult"], "icon": MUTATIONS[k]["icon"]}
            for k in MUTATION_KEYS
        ],
        "traits": [
            {"key": k, "name": TRAITS_DB[k]["name"], "icon": TRAITS_DB[k]["icon"], "percent": TRAITS_DB[k]["percent"]}
            for k in TRAIT_KEYS
        ],
        "free_seconds_left": free_seconds_left,
        "free_case_items": free_case_items,
        "daily_seconds_left": daily_seconds_left,
        "daily_bonus_items": daily_bonus_items,
        "daily_drops": _public_daily_drops(db),
        "global_message": gm_public,
        "active_events": _active_events_public(db),
        "luck_event": _active_luck_public(db),
        "is_admin": _is_admin(user_id),
        "trade_commission": TRADE_COMMISSION,
        "profile": {
            "user_id": user_id,
            "username": user.get("username", ""),
            "first_name": user.get("first_name", ""),
            "photo_url": user.get("photo_url", ""),
            "balance": round(user["balance"], 2),
            "inv_count": len(user["inventory"]),
            "inv_value": inv_value,
        }
    }


@app.post("/api/profile/sync")
def profile_sync(req: ProfileSyncReq):
    if not req.user_id:
        raise HTTPException(status_code=400, detail="Некорректный user_id")
    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)
    user["username"] = (req.username or "")[:64]
    user["first_name"] = (req.first_name or "")[:128]
    user["photo_url"] = (req.photo_url or "")[:512]
    user["last_seen"] = int(time.time())
    github_save_db(db, sha)
    return {"ok": True}


@app.post("/api/topup_request")
def topup_request(req: TopupReq):
    if not req.user_id:
        raise HTTPException(status_code=400, detail="Некорректный user_id")
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
    if req.count not in (1, 3, 5):
        raise HTTPException(status_code=400, detail="Недопустимое количество открытий")

    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)
    case = CASES_DB[req.case_id]

    if case.get("expires_at") and int(time.time()) > case["expires_at"]:
        raise HTTPException(status_code=400, detail="Время действия этого кейса истекло")

    count = int(req.count)
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
    won_items_out = []
    for wid in won_ids:
        mut = roll_mutation(ITEMS_DB[wid]["rarity"])
        inv_id = db["next_inv_id"]
        db["next_inv_id"] += 1
        user["inventory"].append({"inv_id": inv_id, "item_id": wid, "mutation": mut, "traits": []})
        won_inv_ids.append(inv_id)
        won_items_out.append(item_with_traits(wid, mut, []))

    record_daily_drop(db, req.user_id, won_items_out, "case")

    github_save_db(db, sha)
    return {"won_items": won_items_out, "won_inv_ids": won_inv_ids}


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

    mut = roll_mutation(ITEMS_DB[won_item_id]["rarity"])
    user["last_free_case"] = now
    inv_id = db["next_inv_id"]
    db["next_inv_id"] += 1
    user["inventory"].append({"inv_id": inv_id, "item_id": won_item_id, "mutation": mut, "traits": []})

    item_out = item_with_traits(won_item_id, mut, [])
    record_daily_drop(db, req.user_id, [item_out], "free_case")

    github_save_db(db, sha)
    return {"won_items": [item_out], "won_inv_ids": [inv_id]}


def _has_required_tag(user) -> bool:
    parts = [
        user.get("username", "") or "",
        user.get("first_name", "") or "",
    ]
    haystack = " ".join(parts).lower().replace(" ", "").replace("_", "")
    return DAILY_BONUS_REQUIRED_TAG in haystack


@app.post("/api/open_daily_bonus_case")
def open_daily_bonus_case(req: DailyBonusReq):
    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)

    now = int(time.time())
    last_open = user.get("last_daily_bonus", 0)
    if now - last_open < DAILY_BONUS_COOLDOWN:
        left = DAILY_BONUS_COOLDOWN - (now - last_open)
        hours = left // 3600
        mins = (left % 3600) // 60
        raise HTTPException(status_code=400, detail=f"Кейс награды будет доступен через {hours}ч {mins}м")

    if not _has_required_tag(user):
        raise HTTPException(
            status_code=400,
            detail="Чтобы забрать кейс награды, добавьте @BrainDropDropBot в свой Telegram-ник (или имя)."
        )

    item_id = random.choice(DAILY_BONUS_ITEM_IDS)
    coins = random.randint(9, 23)
    mut = roll_mutation(ITEMS_DB[item_id]["rarity"])

    user["last_daily_bonus"] = now
    inv_id = db["next_inv_id"]
    db["next_inv_id"] += 1
    user["inventory"].append({"inv_id": inv_id, "item_id": item_id, "mutation": mut, "traits": []})
    user["balance"] = round(user["balance"] + coins, 2)

    item = item_with_traits(item_id, mut, [])
    record_daily_drop(db, req.user_id, [item], "daily_bonus")

    github_save_db(db, sha)
    return {
        "won_items": [item],
        "won_inv_ids": [inv_id],
        "coins_added": coins,
        "total_value": round(item["price"] + coins, 2)
    }


@app.post("/api/redeem_promo")
def redeem_promo(req: PromoReq):
    code = (req.code or "").strip().upper()
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
        mut = roll_mutation(ITEMS_DB[item_id]["rarity"])
        inv_id = db["next_inv_id"]
        db["next_inv_id"] += 1
        user["inventory"].append({"inv_id": inv_id, "item_id": item_id, "mutation": mut, "traits": []})
        reward_text = f"Предмет: {item_with_traits(item_id, mut, [])['name']}"
        record_daily_drop(db, req.user_id, [item_with_traits(item_id, mut, [])], "promo")
    else:
        raise HTTPException(status_code=400, detail="Неизвестный тип промокода")

    promo["stock"] = max(0, int(promo["stock"]) - 1)
    used_by.append(req.user_id)

    github_save_db(db, sha)
    return {"message": f"Промокод активирован! Награда: {reward_text}"}


@app.post("/api/sell_item")
def sell_item(req: SellItemReq):
    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)

    target_idx = None
    entry = None
    for idx, e in enumerate(user["inventory"]):
        if e["inv_id"] == req.inv_id:
            target_idx = idx
            entry = e
            break

    if target_idx is None or entry["item_id"] not in ITEMS_DB:
        raise HTTPException(status_code=400, detail="Предмет не найден")
    if entry.get("locked"):
        raise HTTPException(status_code=400, detail="Предмет заблокирован заявкой на вывод")

    info = item_with_traits(entry["item_id"], entry.get("mutation", "normal"), entry.get("traits", []))
    price = info["price"]
    user["inventory"].pop(target_idx)
    user["balance"] = round(user["balance"] + price, 2)

    github_save_db(db, sha)
    return {"sold_for": price, "mutation": info["mutation"], "item_name": info["name"]}


@app.post("/api/upgrade")
def do_upgrade(req: UpgradeReq):
    if req.coins_bet < 0:
        raise HTTPException(status_code=400, detail="Некорректная ставка монет")

    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)

    if req.coins_bet > user["balance"]:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    inv_map = {e["inv_id"]: e for e in user["inventory"] if not e.get("locked")}
    items_total_value = 0.0
    for inv_id in req.inv_ids:
        if inv_id not in inv_map or inv_map[inv_id]["item_id"] not in ITEMS_DB:
            raise HTTPException(status_code=400, detail="Ошибка проверки предметов инвентаря")
        e = inv_map[inv_id]
        items_total_value += item_with_traits(e["item_id"], e.get("mutation", "normal"), e.get("traits", []))["price"]

    total_bet = round(items_total_value + req.coins_bet, 2)
    if total_bet <= 0:
        raise HTTPException(status_code=400, detail="Выберите вещи или введите монеты")

    if req.target_type == "item":
        if req.target_item_id not in ITEMS_DB:
            raise HTTPException(status_code=400, detail="Целевой предмет не найден")
        target_mut = req.target_mutation if (req.target_mutation in MUTATIONS) else "normal"
        if not rarity_allows_mutation(ITEMS_DB[req.target_item_id]["rarity"]):
            target_mut = "normal"
        target_value = item_with_traits(req.target_item_id, target_mut, [])["price"]
    else:
        if not req.target_coins or req.target_coins <= total_bet:
            raise HTTPException(status_code=400, detail="Желаемая сумма должна быть больше ставки")
        target_value = float(req.target_coins)
        target_mut = "normal"

    if target_value <= total_bet:
        raise HTTPException(status_code=400, detail="Цель должна быть дороже вашей ставки")

    chance = round((total_bet / target_value) * 92, 2)
    chance = max(1.0, min(75.0, chance))

    user["balance"] = round(user["balance"] - req.coins_bet, 2)
    selected_set = set(req.inv_ids)
    user["inventory"] = [e for e in user["inventory"] if e["inv_id"] not in selected_set]

    roll = random.uniform(0, 100)
    is_win = roll <= chance

    won_item_out = None
    if is_win:
        if req.target_type == "item":
            inv_id = db["next_inv_id"]
            db["next_inv_id"] += 1
            user["inventory"].append({"inv_id": inv_id, "item_id": req.target_item_id, "mutation": target_mut, "traits": []})
            won_item_out = item_with_traits(req.target_item_id, target_mut, [])
            record_daily_drop(db, req.user_id, [won_item_out], "upgrade")
        else:
            user["balance"] = round(user["balance"] + target_value, 2)

    github_save_db(db, sha)
    return {"win": is_win, "chance": chance, "won_item": won_item_out}
# ---------- ЭТАП 7: БАТЛЫ ----------
class BattleCreateReq(BaseModel):
    user_id: str
    case_id: int
    bet: float

class BattleActionReq(BaseModel):
    user_id: str
    battle_id: str


def _battle_public(b: dict) -> dict:
    return {
        "battle_id": b["battle_id"],
        "case_id": b["case_id"],
        "case_name": b.get("case_name", "Кейс"),
        "case_image": b.get("case_image", ""),
        "bet": round(float(b.get("bet", 0)), 2),
        "status": b.get("status", "waiting"),
        "creator_id": b["creator_id"],
        "creator_username": b.get("creator_username", ""),
        "joiner_id": b.get("joiner_id", ""),
        "joiner_username": b.get("joiner_username", ""),
        "creator_rolls": b.get("creator_rolls", []),
        "joiner_rolls": b.get("joiner_rolls", []),
        "creator_total": round(float(b.get("creator_total", 0)), 2),
        "joiner_total": round(float(b.get("joiner_total", 0)), 2),
        "winner_id": b.get("winner_id", ""),
        "created_at": b.get("created_at", 0),
    }


def _roll_battle_case(case: dict) -> dict:
    population = [d["item_id"] for d in case["drops"]]
    weights = [d["weight"] for d in case["drops"]]
    wid = random.choices(population, weights=weights, k=1)[0]
    mut = roll_mutation(ITEMS_DB[wid]["rarity"])
    return item_with_traits(wid, mut, [])


@app.get("/api/battle/list")
def battle_list():
    db, sha = github_load_db()
    db = normalize_db(db)
    battles = db.setdefault("battles", {})
    ordered = sorted(battles.values(), key=lambda x: x.get("created_at", 0), reverse=True)
    return {"battles": [_battle_public(b) for b in ordered[:30]]}


@app.post("/api/battle/create")
def battle_create(req: BattleCreateReq):
    if req.case_id not in CASES_DB:
        raise HTTPException(status_code=400, detail="Кейс не найден")
    bet = round(float(req.bet or 0), 2)
    if bet <= 0:
        raise HTTPException(status_code=400, detail="Укажите ставку больше 0")

    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)
    case = CASES_DB[req.case_id]
    total_cost = round(case["price"] + bet, 2)

    if user["balance"] < total_cost:
        raise HTTPException(
            status_code=400,
            detail=f"Нужно {total_cost} 💰 (кейс {case['price']} + ставка {bet})"
        )

    user["balance"] = round(user["balance"] - total_cost, 2)
    battles = db.setdefault("battles", {})
    bid = str(int(time.time() * 1000))[-6:] + str(random.randint(10, 99))
    battles[bid] = {
        "battle_id": bid,
        "case_id": req.case_id,
        "case_name": case["name"],
        "case_image": case.get("image", ""),
        "bet": bet,
        "status": "waiting",
        "creator_id": req.user_id,
        "creator_username": user.get("username") or user.get("first_name") or req.user_id,
        "joiner_id": "",
        "joiner_username": "",
        "creator_rolls": [],
        "joiner_rolls": [],
        "creator_total": 0.0,
        "joiner_total": 0.0,
        "winner_id": "",
        "created_at": int(time.time()),
    }
    github_save_db(db, sha)
    return {"ok": True, "battle_id": bid}


@app.post("/api/battle/join")
def battle_join(req: BattleActionReq):
    db, sha = github_load_db()
    db = normalize_db(db)
    battles = db.setdefault("battles", {})
    b = battles.get(req.battle_id)
    if not b:
        raise HTTPException(status_code=404, detail="Батл не найден")
    if b["status"] != "waiting":
        raise HTTPException(status_code=400, detail="Батл уже начался или завершён")
    if b["creator_id"] == req.user_id:
        raise HTTPException(status_code=400, detail="Нельзя войти в свой же батл")

    case = CASES_DB.get(b["case_id"])
    if not case:
        raise HTTPException(status_code=400, detail="Кейс батла недоступен")

    user = ensure_user(db, req.user_id)
    total_cost = round(case["price"] + b["bet"], 2)
    if user["balance"] < total_cost:
        raise HTTPException(
            status_code=400,
            detail=f"Нужно {total_cost} 💰 (кейс {case['price']} + ставка {b['bet']})"
        )

    user["balance"] = round(user["balance"] - total_cost, 2)
    b["joiner_id"] = req.user_id
    b["joiner_username"] = user.get("username") or user.get("first_name") or req.user_id
    b["status"] = "running"
    github_save_db(db, sha)
    return {"ok": True, "battle": _battle_public(b)}


@app.post("/api/battle/cancel")
def battle_cancel(req: BattleActionReq):
    db, sha = github_load_db()
    db = normalize_db(db)
    battles = db.setdefault("battles", {})
    b = battles.get(req.battle_id)
    if not b:
        raise HTTPException(status_code=404, detail="Батл не найден")
    if b["creator_id"] != req.user_id:
        raise HTTPException(status_code=403, detail="Отменить может только создатель")
    if b["status"] != "waiting":
        raise HTTPException(status_code=400, detail="Нельзя отменить уже начатый батл")

    case = CASES_DB.get(b["case_id"], {"price": 0})
    refund = round(case["price"] + b["bet"], 2)
    creator = ensure_user(db, req.user_id)
    creator["balance"] = round(creator["balance"] + refund, 2)
    b["status"] = "cancelled"
    github_save_db(db, sha)
    return {"ok": True, "refund": refund}


@app.post("/api/battle/open")
def battle_open(req: BattleActionReq):
    db, sha = github_load_db()
    db = normalize_db(db)
    battles = db.setdefault("battles", {})
    b = battles.get(req.battle_id)
    if not b:
        raise HTTPException(status_code=404, detail="Батл не найден")
    if b["status"] != "running":
        raise HTTPException(status_code=400, detail="Батл не в статусе открытия")
    if req.user_id not in (b["creator_id"], b["joiner_id"]):
        raise HTTPException(status_code=403, detail="Вы не участник этого батла")

    case = CASES_DB.get(b["case_id"])
    if not case:
        raise HTTPException(status_code=400, detail="Кейс не найден")

    if req.user_id == b["creator_id"]:
        if b["creator_rolls"]:
            raise HTTPException(status_code=400, detail="Вы уже открыли свой кейс")
        item = _roll_battle_case(case)
        b["creator_rolls"] = [item]
        b["creator_total"] = item["price"]
    else:
        if b["joiner_rolls"]:
            raise HTTPException(status_code=400, detail="Вы уже открыли свой кейс")
        item = _roll_battle_case(case)
        b["joiner_rolls"] = [item]
        b["joiner_total"] = item["price"]

    # Если оба открыли — определяем победителя и отдаём оба предмета + обе ставки
    if b["creator_rolls"] and b["joiner_rolls"]:
        c_tot = float(b["creator_total"])
        j_tot = float(b["joiner_total"])
        if c_tot > j_tot:
            winner_id = b["creator_id"]
        elif j_tot > c_tot:
            winner_id = b["joiner_id"]
        else:
            winner_id = random.choice([b["creator_id"], b["joiner_id"]])

        b["winner_id"] = winner_id
        b["status"] = "finished"
        winner = ensure_user(db, winner_id)
        winner["balance"] = round(winner["balance"] + b["bet"] * 2, 2)

        all_won = b["creator_rolls"] + b["joiner_rolls"]
        for it in all_won:
            inv_id = db["next_inv_id"]
            db["next_inv_id"] += 1
            winner["inventory"].append({
                "inv_id": inv_id,
                "item_id": it["id"],
                "mutation": it.get("mutation", "normal"),
                "traits": [t["key"] for t in it.get("traits", [])],
            })
        record_daily_drop(db, winner_id, all_won, "battle")

    github_save_db(db, sha)
    return {"ok": True, "battle": _battle_public(b)}


@app.get("/api/battle/{battle_id}")
def battle_detail(battle_id: str):
    db, sha = github_load_db()
    db = normalize_db(db)
    b = db.setdefault("battles", {}).get(battle_id)
    if not b:
        raise HTTPException(status_code=404, detail="Батл не найден")
    return _battle_public(b)


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
    if req.user_id in ACTIVE_CRASH_GAMES:
        raise HTTPException(status_code=400, detail="У вас уже есть активная игра. Дождитесь завершения.")

    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)

    if req.coins_bet > user["balance"]:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    inv_map = {e["inv_id"]: e for e in user["inventory"] if not e.get("locked")}
    bet_items = []
    items_total_value = 0.0

    for inv_id in req.inv_ids:
        if inv_id not in inv_map or inv_map[inv_id]["item_id"] not in ITEMS_DB:
            raise HTTPException(status_code=400, detail="Ошибка проверки предметов инвентаря")
        e = inv_map[inv_id]
        info = item_with_traits(e["item_id"], e.get("mutation", "normal"), e.get("traits", []))
        items_total_value += info["price"]
        bet_items.append({"inv_id": inv_id, "item_id": e["item_id"], "mutation": e.get("mutation", "normal"), "traits": e.get("traits", [])})

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
    if not math.isfinite(req.multiplier) or req.multiplier < 1.0:
        raise HTTPException(status_code=400, detail="Некорректный множитель")

    game = ACTIVE_CRASH_GAMES.pop(req.user_id, None)
    if not game:
        raise HTTPException(status_code=400, detail="Активная игра не найдена или ракета уже взорвалась")

    if req.multiplier > game["crash_point"]:
        raise HTTPException(status_code=400, detail="Ракета уже взорвалась!")

    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)

    total_win_value = round(game["total_bet"] * req.multiplier, 2)
    won_item, returned_items, coins_added, recorded = _payout_like_crash(
        db, user, total_win_value, game["bet_items"], game["items_value"]
    )

    if recorded:
        record_daily_drop(db, req.user_id, recorded, "crash")

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
    multipliers_table = {1: 1.85, 3: 5.5, 5: 18.0, 7: 60.0, 9: 200.0, 11: 750.0}
    return multipliers_table.get(matches, 1.85)


@app.post("/api/colordice/roll")
def play_color_dice(req: ColorDiceReq):
    color = (req.chosen_color or "").strip().lower()
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

    inv_map = {e["inv_id"]: e for e in user["inventory"] if not e.get("locked")}
    items_total_value = 0.0
    for inv_id in req.inv_ids:
        if inv_id not in inv_map or inv_map[inv_id]["item_id"] not in ITEMS_DB:
            raise HTTPException(status_code=400, detail="Ошибка проверки предметов инвентаря")
        e = inv_map[inv_id]
        items_total_value += item_with_traits(e["item_id"], e.get("mutation", "normal"), e.get("traits", []))["price"]

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


MINES_GRID = 25


def mines_multiplier(mines: int, opened: int) -> float:
    if opened <= 0:
        return 1.0
    safe_total = MINES_GRID - mines
    if opened > safe_total:
        opened = safe_total
    p = 1.0
    for i in range(opened):
        p *= (safe_total - i) / (MINES_GRID - i)
    mult = (1.0 / p) * 0.95 if p > 0 else 0.0
    return round(max(1.0, mult), 2)


@app.post("/api/mines/start")
def mines_start(req: MinesStartReq):
    if req.coins_bet < 0:
        raise HTTPException(status_code=400, detail="Некорректная ставка монет")
    if req.mines < 1 or req.mines > 24:
        raise HTTPException(status_code=400, detail="Количество мин: от 1 до 24")
    if req.user_id in ACTIVE_MINES_GAMES:
        raise HTTPException(status_code=400, detail="У вас уже есть активная игра в Мины")

    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)

    if req.coins_bet > user["balance"]:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    inv_map = {e["inv_id"]: e for e in user["inventory"] if not e.get("locked")}
    bet_items = []
    items_total_value = 0.0
    for inv_id in req.inv_ids:
        if inv_id not in inv_map or inv_map[inv_id]["item_id"] not in ITEMS_DB:
            raise HTTPException(status_code=400, detail="Ошибка проверки предметов инвентаря")
        e = inv_map[inv_id]
        info = item_with_traits(e["item_id"], e.get("mutation", "normal"), e.get("traits", []))
        items_total_value += info["price"]
        bet_items.append({"inv_id": inv_id, "item_id": e["item_id"], "mutation": e.get("mutation", "normal"), "traits": e.get("traits", [])})

    total_bet = round(items_total_value + req.coins_bet, 2)
    if total_bet <= 0:
        raise HTTPException(status_code=400, detail="Сделайте ставку монетами или вещами")

    user["balance"] = round(user["balance"] - req.coins_bet, 2)
    selected_set = set(req.inv_ids)
    user["inventory"] = [e for e in user["inventory"] if e["inv_id"] not in selected_set]
    github_save_db(db, sha)

    field = set(random.sample(range(MINES_GRID), req.mines))
    ACTIVE_MINES_GAMES[req.user_id] = {
        "mines": req.mines,
        "field": field,
        "opened": [],
        "bet_items": bet_items,
        "items_value": items_total_value,
        "coins_bet": req.coins_bet,
        "total_bet": total_bet
    }
    return {"ok": True, "total_bet": total_bet, "mines": req.mines}


@app.post("/api/mines/open")
def mines_open(req: MinesOpenReq):
    game = ACTIVE_MINES_GAMES.get(req.user_id)
    if not game:
        raise HTTPException(status_code=400, detail="Активная игра не найдена")
    if req.cell < 0 or req.cell >= MINES_GRID:
        raise HTTPException(status_code=400, detail="Некорректная клетка")
    if req.cell in game["opened"]:
        raise HTTPException(status_code=400, detail="Клетка уже открыта")

    if req.cell in game["field"]:
        ACTIVE_MINES_GAMES.pop(req.user_id, None)
        return {"boom": True, "cell": req.cell, "field": sorted(list(game["field"]))}

    game["opened"].append(req.cell)
    opened = len(game["opened"])
    mult = mines_multiplier(game["mines"], opened)
    potential = round(game["total_bet"] * mult, 2)
    return {"boom": False, "cell": req.cell, "opened": opened, "multiplier": mult, "potential_win": potential}


@app.post("/api/mines/cashout")
def mines_cashout(req: MinesCashoutReq):
    game = ACTIVE_MINES_GAMES.pop(req.user_id, None)
    if not game:
        raise HTTPException(status_code=400, detail="Активная игра не найдена")
    opened = len(game["opened"])
    if opened <= 0:
        raise HTTPException(status_code=400, detail="Откройте хотя бы одну клетку")

    mult = mines_multiplier(game["mines"], opened)
    total_win_value = round(game["total_bet"] * mult, 2)

    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)

    won_item, returned_items, coins_added, recorded = _payout_like_crash(
        db, user, total_win_value, game["bet_items"], game["items_value"]
    )

    if recorded:
        record_daily_drop(db, req.user_id, recorded, "mines")

    github_save_db(db, sha)
    return {
        "total_win": total_win_value,
        "multiplier": mult,
        "won_item": won_item,
        "returned_items": returned_items,
        "coins_added": coins_added
    }


PLINKO_ROWS = 12
PLINKO_MULTS = [29.0, 14.0, 6.0, 3.0, 1.5, 0.7, 0.4, 0.7, 1.5, 3.0, 6.0, 14.0, 29.0]


def _payout_like_crash(db, user, total_win_value: float, bet_items: list, items_value: float):
    max_item_price = max(it["price"] for it in ITEMS_DB.values())
    won_item = None
    returned_items = []
    coins_added = 0.0
    recorded = []

    if total_win_value > max_item_price:
        for item_entry in bet_items:
            user["inventory"].append(item_entry)
            info = item_with_traits(item_entry["item_id"], item_entry.get("mutation", "normal"), item_entry.get("traits", []))
            returned_items.append(info)
            recorded.append(info)
        diff = round(total_win_value - items_value, 2)
        user["balance"] = round(user["balance"] + diff, 2)
        coins_added = diff
    else:
        affordable = [it for it in ITEMS_DB.values() if it["price"] <= total_win_value]
        if affordable:
            best_item = max(affordable, key=lambda x: x["price"])
            mut = roll_mutation(best_item["rarity"])
            info = item_with_traits(best_item["id"], mut, [])
            while info["price"] > total_win_value and mut != "normal":
                mut = "normal"
                info = item_with_traits(best_item["id"], mut, [])
            inv_id = db["next_inv_id"]
            db["next_inv_id"] += 1
            user["inventory"].append({"inv_id": inv_id, "item_id": best_item["id"], "mutation": mut, "traits": []})
            won_item = info
            recorded.append(info)
            remainder = round(total_win_value - info["price"], 2)
            user["balance"] = round(user["balance"] + remainder, 2)
            coins_added = remainder
        else:
            user["balance"] = round(user["balance"] + total_win_value, 2)
            coins_added = total_win_value

    return won_item, returned_items, coins_added, recorded


@app.post("/api/plinko/play")
def plinko_play(req: PlinkoPlayReq):
    if req.coins_bet < 0:
        raise HTTPException(status_code=400, detail="Некорректная ставка монет")

    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)

    if req.coins_bet > user["balance"]:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    inv_map = {e["inv_id"]: e for e in user["inventory"] if not e.get("locked")}
    bet_items = []
    items_value = 0.0
    for inv_id in req.inv_ids:
        if inv_id not in inv_map or inv_map[inv_id]["item_id"] not in ITEMS_DB:
            raise HTTPException(status_code=400, detail="Ошибка проверки предметов инвентаря")
        e = inv_map[inv_id]
        info = item_with_traits(e["item_id"], e.get("mutation", "normal"), e.get("traits", []))
        items_value += info["price"]
        bet_items.append({"inv_id": inv_id, "item_id": e["item_id"], "mutation": e.get("mutation", "normal"), "traits": e.get("traits", [])})

    total_bet = round(items_value + req.coins_bet, 2)
    if total_bet <= 0:
        raise HTTPException(status_code=400, detail="Сделайте ставку монетами или вещами")

    user["balance"] = round(user["balance"] - req.coins_bet, 2)
    selected_set = set(req.inv_ids)
    user["inventory"] = [e for e in user["inventory"] if e["inv_id"] not in selected_set]

    path = [random.randint(0, 1) for _ in range(PLINKO_ROWS)]
    slot = sum(path)
    mult = PLINKO_MULTS[slot]
    total_win_value = round(total_bet * mult, 2)

    won_item, returned_items, coins_added, recorded = _payout_like_crash(
        db, user, total_win_value, bet_items, items_value
    )

    if recorded:
        record_daily_drop(db, req.user_id, recorded, "plinko")

    github_save_db(db, sha)
    return {
        "path": path,
        "slot": slot,
        "multiplier": mult,
        "total_bet": total_bet,
        "total_win": total_win_value,
        "won_item": won_item,
        "returned_items": returned_items,
        "coins_added": coins_added,
    }


TOWER_FLOORS = 5
TOWER_COLS = 5


def tower_multiplier(floor: int) -> float:
    if floor <= 0:
        return 1.0
    base = (TOWER_COLS / (TOWER_COLS - 1)) ** floor
    return round(base * 0.95, 2)


@app.post("/api/tower/start")
def tower_start(req: TowerStartReq):
    if req.coins_bet < 0:
        raise HTTPException(status_code=400, detail="Некорректная ставка монет")
    if req.user_id in ACTIVE_TOWER_GAMES:
        raise HTTPException(status_code=400, detail="У вас уже есть активная игра в Башню")

    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)

    if req.coins_bet > user["balance"]:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    inv_map = {e["inv_id"]: e for e in user["inventory"] if not e.get("locked")}
    bet_items = []
    items_total_value = 0.0
    for inv_id in req.inv_ids:
        if inv_id not in inv_map or inv_map[inv_id]["item_id"] not in ITEMS_DB:
            raise HTTPException(status_code=400, detail="Ошибка проверки предметов инвентаря")
        e = inv_map[inv_id]
        info = item_with_traits(e["item_id"], e.get("mutation", "normal"), e.get("traits", []))
        items_total_value += info["price"]
        bet_items.append({"inv_id": inv_id, "item_id": e["item_id"], "mutation": e.get("mutation", "normal"), "traits": e.get("traits", [])})

    total_bet = round(items_total_value + req.coins_bet, 2)
    if total_bet <= 0:
        raise HTTPException(status_code=400, detail="Сделайте ставку монетами или вещами")

    user["balance"] = round(user["balance"] - req.coins_bet, 2)
    selected_set = set(req.inv_ids)
    user["inventory"] = [e for e in user["inventory"] if e["inv_id"] not in selected_set]
    github_save_db(db, sha)

    field = [random.randint(0, TOWER_COLS - 1) for _ in range(TOWER_FLOORS)]
    ACTIVE_TOWER_GAMES[req.user_id] = {
        "field": field,
        "opened": [],
        "bet_items": bet_items,
        "items_value": items_total_value,
        "coins_bet": req.coins_bet,
        "total_bet": total_bet
    }
    return {"ok": True, "total_bet": total_bet, "floors": TOWER_FLOORS, "cols": TOWER_COLS}


@app.post("/api/tower/open")
def tower_open(req: TowerOpenReq):
    game = ACTIVE_TOWER_GAMES.get(req.user_id)
    if not game:
        raise HTTPException(status_code=400, detail="Активная игра не найдена")
    floor = len(game["opened"])
    if floor >= TOWER_FLOORS:
        raise HTTPException(status_code=400, detail="Все этажи пройдены — забирайте выигрыш")
    if req.cell < 0 or req.cell >= TOWER_COLS:
        raise HTTPException(status_code=400, detail="Некорректная клетка")

    if req.cell == game["field"][floor]:
        ACTIVE_TOWER_GAMES.pop(req.user_id, None)
        return {"boom": True, "floor": floor, "cell": req.cell, "field": game["field"]}

    game["opened"].append(req.cell)
    passed = len(game["opened"])
    mult = tower_multiplier(passed)
    potential = round(game["total_bet"] * mult, 2)
    return {
        "boom": False,
        "floor": floor,
        "cell": req.cell,
        "passed_floors": passed,
        "multiplier": mult,
        "potential_win": potential,
        "finished": passed >= TOWER_FLOORS
    }


@app.post("/api/tower/cashout")
def tower_cashout(req: TowerCashoutReq):
    game = ACTIVE_TOWER_GAMES.pop(req.user_id, None)
    if not game:
        raise HTTPException(status_code=400, detail="Активная игра не найдена")
    passed = len(game["opened"])
    if passed <= 0:
        raise HTTPException(status_code=400, detail="Пройдите хотя бы один этаж")

    mult = tower_multiplier(passed)
    total_win_value = round(game["total_bet"] * mult, 2)

    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)

    won_item, returned_items, coins_added, recorded = _payout_like_crash(
        db, user, total_win_value, game["bet_items"], game["items_value"]
    )

    if recorded:
        record_daily_drop(db, req.user_id, recorded, "tower")

    github_save_db(db, sha)
    return {
        "total_win": total_win_value,
        "multiplier": mult,
        "won_item": won_item,
        "returned_items": returned_items,
        "coins_added": coins_added,
        "passed_floors": passed
    }


# ---------- ЭТАП 4: АДМИН ----------
# =========================================================
# LIMBO
# =========================================================
LIMBO_HOUSE_EDGE = 0.95  # 5% house edge
LIMBO_MIN_TARGET = 1.01
LIMBO_MAX_TARGET = 100.0


def limbo_win_chance(target_multiplier: float) -> float:
    """Шанс победы = (1 / target) * house_edge * 100, ограничен 1..99%."""
    if target_multiplier <= 0:
        return 0.0
    chance = (1.0 / target_multiplier) * LIMBO_HOUSE_EDGE * 100.0
    return max(1.0, min(99.0, round(chance, 2)))


def limbo_roll() -> float:
    """Возвращает сгенерированный множитель. Распределение: P(X >= t) = edge / t."""
    u = random.random()
    if u < 0.0001:
        u = 0.0001
    roll = LIMBO_HOUSE_EDGE / u
    return round(max(1.0, min(1000.0, roll)), 2)


@app.post("/api/limbo/play")
def limbo_play(req: LimboReq):
    if req.coins_bet < 0:
        raise HTTPException(status_code=400, detail="Некорректная ставка монет")
    target = float(req.target_multiplier or 0)
    if target < LIMBO_MIN_TARGET or target > LIMBO_MAX_TARGET:
        raise HTTPException(status_code=400, detail=f"Целевой множитель: от {LIMBO_MIN_TARGET} до {LIMBO_MAX_TARGET}")

    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)

    if req.coins_bet > user["balance"]:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    inv_map = {e["inv_id"]: e for e in user["inventory"] if not e.get("locked")}
    bet_items = []
    items_value = 0.0
    for inv_id in req.inv_ids or []:
        if inv_id not in inv_map or inv_map[inv_id]["item_id"] not in ITEMS_DB:
            raise HTTPException(status_code=400, detail="Ошибка проверки предметов инвентаря")
        e = inv_map[inv_id]
        info = item_with_traits(e["item_id"], e.get("mutation", "normal"), e.get("traits", []))
        items_value += info["price"]
        bet_items.append({"inv_id": inv_id, "item_id": e["item_id"], "mutation": e.get("mutation", "normal"), "traits": e.get("traits", [])})

    total_bet = round(items_value + req.coins_bet, 2)
    if total_bet <= 0:
        raise HTTPException(status_code=400, detail="Сделайте ставку монетами или вещами")

    user["balance"] = round(user["balance"] - req.coins_bet, 2)
    selected_set = set(req.inv_ids or [])
    user["inventory"] = [e for e in user["inventory"] if e["inv_id"] not in selected_set]

    roll = limbo_roll()
    is_win = roll >= target
    chance = limbo_win_chance(target)

    total_win_value = 0.0
    won_item = None
    returned_items = []
    coins_added = 0.0
    recorded = []

    if is_win:
        total_win_value = round(total_bet * target, 2)
        won_item, returned_items, coins_added, recorded = _payout_like_crash(
            db, user, total_win_value, bet_items, items_value
        )
        if recorded:
            record_daily_drop(db, req.user_id, recorded, "limbo")
    else:
        # предметы и монеты уже списаны — ставка сгорела
        pass

    github_save_db(db, sha)
    return {
        "roll": roll,
        "target": target,
        "chance": chance,
        "win": is_win,
        "total_bet": total_bet,
        "total_win": total_win_value,
        "won_item": won_item,
        "returned_items": returned_items,
        "coins_added": coins_added,
    }


# =========================================================
# WHEEL (Колесо)
# =========================================================
# Каждый элемент — множитель сегмента. 0 = пустой сектор.
WHEEL_SEGMENTS = {
    "low":    [0, 1.2, 1.5, 1.2, 2.0, 1.2, 1.5, 1.2, 0, 1.5, 1.2, 3.0, 1.2, 1.5, 0, 1.2, 1.5, 1.2, 2.0, 1.2],
    "medium": [0, 1.5, 2.0, 0, 3.0, 1.5, 0, 5.0, 2.0, 0, 1.5, 10.0, 0, 2.0, 1.5, 0, 3.0, 0, 1.5, 0],
    "high":   [0, 0, 3.0, 0, 5.0, 0, 10.0, 0, 0, 20.0, 0, 50.0, 0, 10.0, 0, 5.0, 0, 3.0, 0, 0],
}


def wheel_multiplier(risk: str) -> float:
    risk = (risk or "medium").lower()
    segments = WHEEL_SEGMENTS.get(risk, WHEEL_SEGMENTS["medium"])
    return float(random.choice(segments))


@app.post("/api/wheel/spin")
def wheel_spin(req: WheelReq):
    if req.coins_bet < 0:
        raise HTTPException(status_code=400, detail="Некорректная ставка монет")
    risk = (req.risk or "medium").lower()
    if risk not in WHEEL_SEGMENTS:
        raise HTTPException(status_code=400, detail="risk: low | medium | high")

    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)

    if req.coins_bet > user["balance"]:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    inv_map = {e["inv_id"]: e for e in user["inventory"] if not e.get("locked")}
    bet_items = []
    items_value = 0.0
    for inv_id in req.inv_ids or []:
        if inv_id not in inv_map or inv_map[inv_id]["item_id"] not in ITEMS_DB:
            raise HTTPException(status_code=400, detail="Ошибка проверки предметов инвентаря")
        e = inv_map[inv_id]
        info = item_with_traits(e["item_id"], e.get("mutation", "normal"), e.get("traits", []))
        items_value += info["price"]
        bet_items.append({"inv_id": inv_id, "item_id": e["item_id"], "mutation": e.get("mutation", "normal"), "traits": e.get("traits", [])})

    total_bet = round(items_value + req.coins_bet, 2)
    if total_bet <= 0:
        raise HTTPException(status_code=400, detail="Сделайте ставку монетами или вещами")

    user["balance"] = round(user["balance"] - req.coins_bet, 2)
    selected_set = set(req.inv_ids or [])
    user["inventory"] = [e for e in user["inventory"] if e["inv_id"] not in selected_set]

    segments = WHEEL_SEGMENTS[risk]
    seg_index = random.randrange(len(segments))
    multiplier = float(segments[seg_index])

    total_win_value = 0.0
    won_item = None
    returned_items = []
    coins_added = 0.0
    recorded = []

    if multiplier > 0:
        total_win_value = round(total_bet * multiplier, 2)
        won_item, returned_items, coins_added, recorded = _payout_like_crash(
            db, user, total_win_value, bet_items, items_value
        )
        if recorded:
            record_daily_drop(db, req.user_id, recorded, "wheel")

    github_save_db(db, sha)
    return {
        "risk": risk,
        "segments": segments,
        "segment_index": seg_index,
        "multiplier": multiplier,
        "win": multiplier > 0,
        "total_bet": total_bet,
        "total_win": total_win_value,
        "won_item": won_item,
        "returned_items": returned_items,
        "coins_added": coins_added,
    }


# =========================================================
# KENO
# =========================================================
KENO_MAX = 80
KENO_DRAW = 20

# Таблица выплат (множитель от ставки). Ключ — сколько чисел выбрано,
# значение — словарь {кол-во совпадений: множитель}.
# Значения подобраны так, чтобы house edge был ~5–10%. При желании можно менять.
KENO_PAYOUTS = {
    1:  {0: 0.0, 1: 3.0},
    2:  {0: 0.0, 1: 1.5, 2: 5.0},
    3:  {0: 0.0, 1: 1.0, 2: 3.0, 3: 15.0},
    4:  {0: 0.0, 1: 0.5, 2: 2.0, 3: 8.0, 4: 50.0},
    5:  {0: 0.0, 1: 0.5, 2: 1.5, 3: 5.0, 4: 20.0, 5: 150.0},
    6:  {0: 0.0, 1: 0.5, 2: 1.2, 3: 3.0, 4: 10.0, 5: 50.0, 6: 500.0},
    7:  {0: 0.0, 1: 0.5, 2: 1.0, 3: 2.5, 4: 6.0, 5: 20.0, 6: 80.0, 7: 800.0},
    8:  {0: 0.0, 1: 0.5, 2: 1.0, 3: 2.0, 4: 5.0, 5: 15.0, 6: 50.0, 7: 200.0, 8: 1000.0},
    9:  {0: 0.0, 1: 0.5, 2: 0.8, 3: 1.5, 4: 3.0, 5: 8.0, 6: 25.0, 7: 80.0, 8: 400.0, 9: 2000.0},
    10: {0: 0.0, 1: 0.5, 2: 0.8, 3: 1.5, 4: 2.5, 5: 6.0, 6: 18.0, 7: 50.0, 8: 200.0, 9: 1000.0, 10: 5000.0},
}


def keno_payout(picked_count: int, matches: int) -> float:
    table = KENO_PAYOUTS.get(picked_count)
    if not table:
        return 0.0
    return float(table.get(matches, 0.0))

# =========================================================
# FUSE (Фьюз) — 4 предмета → 1 результат
# =========================================================
FUSE_SLOTS = 4
FUSE_SPREAD = {
    "common":    2.0,
    "rare":      3.0,
    "epic":      4.0,
    "legendary": 5.0,
    "mythic":    5.0,   # как у legendary
}
FUSE_RARITY_ORDER = ["common", "rare", "epic", "legendary", "mythic"]


def fuse_base_rarity(rarities: list) -> str:
    """Самая высокая редкость среди предметов."""
    best = "common"
    for r in rarities:
        r = (r or "").lower()
        if r in FUSE_RARITY_ORDER and FUSE_RARITY_ORDER.index(r) > FUSE_RARITY_ORDER.index(best):
            best = r
    return best


def fuse_roll_multiplier(base_rarity: str) -> float:
    """Случайный коэффициент от 1/spread до spread. Логарифмически равномерно,
    чтобы 'остаться' (×1) был самым вероятным."""
    spread = FUSE_SPREAD.get(base_rarity, 2.0)
    # генерируем u в [0,1), коэффициент = spread^(2u-1) → от 1/spread до spread
    u = random.random()
    mult = spread ** (2.0 * u - 1.0)
    return round(mult, 4)


def fuse_pick_item_for_value(target_value: float, prefer_rarity: str = None) -> dict:
    """Выбирает предмет, цена которого максимально близка к target_value,
    но не превышает её. Если prefer_rarity задан — сначала ищем среди этой редкости.
    Если ничего не подошло — возвращает None."""
    if target_value <= 0:
        return None
    candidates = []
    for item in ITEMS_DB.values():
        info = item_with_traits(item["id"], "normal", [])
        if info["price"] <= target_value + 1e-9:
            candidates.append(info)
    if not candidates:
        return None
    if prefer_rarity:
        preferred = [c for c in candidates if (c.get("rarity") or "").lower() == prefer_rarity]
        if preferred:
            candidates = preferred
    # максимально близкий к target_value
    best = max(candidates, key=lambda c: c["price"])
    return best


@app.post("/api/fuse/play")
def fuse_play(req: FuseReq):
    inv_ids = list(dict.fromkeys(int(x) for x in (req.inv_ids or [])))
    if len(inv_ids) != FUSE_SLOTS:
        raise HTTPException(status_code=400, detail=f"Нужно ровно {FUSE_SLOTS} предмета для фьюза")

    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)

    inv_map = {e["inv_id"]: e for e in user["inventory"]}
    picked = []
    total_bet = 0.0
    rarities = []

    for iid in inv_ids:
        e = inv_map.get(iid)
        if not e:
            raise HTTPException(status_code=400, detail=f"Предмет {iid} не найден")
        if e.get("locked"):
            raise HTTPException(status_code=400, detail=f"Предмет {iid} заблокирован (вывод)")
        info = item_with_traits(e["item_id"], e.get("mutation", "normal"), e.get("traits", []))
        total_bet += info["price"]
        rarities.append(info["rarity"])
        picked.append(e)

    total_bet = round(total_bet, 2)
    if total_bet <= 0:
        raise HTTPException(status_code=400, detail="Сумма ставки должна быть больше 0")

    # Забираем 4 предмета из инвентаря
    selected_set = set(inv_ids)
    user["inventory"] = [e for e in user["inventory"] if e["inv_id"] not in selected_set]

    base_rarity = fuse_base_rarity(rarities)
    multiplier = fuse_roll_multiplier(base_rarity)
    target_value = round(total_bet * multiplier, 2)

    # Ищем предмет под целевую сумму (сначала той же редкости, что и базовая, если получилось "остаться")
    want_rarity = None
    if abs(multiplier - 1.0) < 0.05:
        want_rarity = base_rarity
    chosen = fuse_pick_item_for_value(target_value, prefer_rarity=want_rarity)

    won_item = None
    coins_added = 0.0
    returned_items = []
    recorded = []

    if chosen:
        inv_id = db["next_inv_id"]
        db["next_inv_id"] += 1
        user["inventory"].append({
            "inv_id": inv_id,
            "item_id": chosen["id"],
            "mutation": "normal",
            "traits": [],
        })
        won_item = chosen
        coins_added = round(target_value - chosen["price"], 2)
        if coins_added > 0:
            user["balance"] = round(user["balance"] + coins_added, 2)
        recorded = [chosen]
    else:
        # предмета под сумму нет (слишком маленькая сумма) — всё монетами
        user["balance"] = round(user["balance"] + target_value, 2)
        coins_added = target_value

    record_daily_drop(db, req.user_id, recorded, "fuse")
    github_save_db(db, sha)

    return {
        "base_rarity": base_rarity,
        "multiplier": multiplier,
        "total_bet": total_bet,
        "target_value": target_value,
        "won_item": won_item,
        "coins_added": coins_added,
    }
# =========================================================
# ПАДАЮЩАЯ КИРКА
# =========================================================
@app.post("/api/pickaxe/drop")
def pickaxe_drop(req: PickaxeDropReq):
    tier = (req.pickaxe_tier or "wooden").lower()
    if tier not in PICKAXES:
        raise HTTPException(status_code=400, detail="Неизвестный тир кирки")
    if req.coins_bet < 0:
        raise HTTPException(status_code=400, detail="Некорректная ставка монет")

    pick_cfg = PICKAXES[tier]
    pick_cost = float(pick_cfg["cost"])

    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)

    # Проверка монет: стоимость кирки + ставка монетами
    need_coins = round(pick_cost + req.coins_bet, 2)
    if user["balance"] < need_coins:
        raise HTTPException(status_code=400, detail=f"Нужно {need_coins} 💰 (кирка {pick_cost} + ставка {req.coins_bet})")

    # Собираем вещи в ставку
    inv_map = {e["inv_id"]: e for e in user["inventory"] if not e.get("locked")}
    bet_items = []
    items_value = 0.0
    for inv_id in req.inv_ids or []:
        if inv_id not in inv_map or inv_map[inv_id]["item_id"] not in ITEMS_DB:
            raise HTTPException(status_code=400, detail="Ошибка проверки предметов инвентаря")
        e = inv_map[inv_id]
        info = item_with_traits(e["item_id"], e.get("mutation", "normal"), e.get("traits", []))
        items_value += info["price"]
        bet_items.append(e)

    total_bet = round(items_value + req.coins_bet, 2)
    if total_bet <= 0:
        raise HTTPException(status_code=400, detail="Сделайте ставку монетами или вещами")

    # Списываем: кирка (невозвратно) + ставка монетами + вещи из инвентаря
    user["balance"] = round(user["balance"] - need_coins, 2)
    selected_set = set(req.inv_ids or [])
    user["inventory"] = [e for e in user["inventory"] if e["inv_id"] not in selected_set]

    # Симуляция падения
    hp = int(pick_cfg["hp"])
    damage = int(pick_cfg["damage"])
    depth = 0
    ores_collected = {}   # key -> count
    events_log = []
    tnt_pending = 0
    arrow_pending = 0

    while hp > 0 and depth < PICKAXE_MAX_DEPTH:
        cell = pickaxe_roll_cell()
        depth += 1

        if cell["type"] == "empty":
            hp -= 1  # лёгкий удар
            events_log.append({"depth": depth, "type": "empty"})
            continue

        if cell["type"] == "ore":
            ores_collected[cell["key"]] = ores_collected.get(cell["key"], 0) + 1
            hp -= 2
            events_log.append({"depth": depth, "type": "ore", "key": cell["key"]})
            continue

        # special
        sp = cell["key"]
        if sp == "tnt":
            # взрыв: пролетаем 3 блока без траты HP
            hp -= 0
            tnt_pending += 3
            events_log.append({"depth": depth, "type": "tnt"})
            # проматываем tnt_pending блоков (собираем руды без HP)
            while tnt_pending > 0 and depth < PICKAXE_MAX_DEPTH:
                depth += 1
                tnt_pending -= 1
                inner = pickaxe_roll_cell()
                if inner["type"] == "ore":
                    ores_collected[inner["key"]] = ores_collected.get(inner["key"], 0) + 1
                events_log.append({"depth": depth, "type": "tnt_pass", "inner": inner})
            continue
        if sp == "workbench":
            # верстак: +50 HP
            hp = min(int(pick_cfg["hp"]), hp + 50)
            events_log.append({"depth": depth, "type": "workbench"})
            continue
        if sp == "arrow":
            # стрелка: +1 урон на 5 блоков
            damage += 1
            arrow_pending = 5
            events_log.append({"depth": depth, "type": "arrow"})
            continue

    # Сумма руд
    ores_total_value = 0.0
    ores_summary = []
    for key, cnt in ores_collected.items():
        cfg = ORES[key]
        val = cfg["value"] * cnt
        ores_total_value += val
        ores_summary.append({"key": key, "name": cfg["name"], "count": cnt, "value": val, "icon": cfg["icon"], "fallback": cfg["fallback"]})

    # Множитель глубины
    mult = round(1.0 + depth * 0.05, 4)
    total_win_value = round(total_bet * mult + ores_total_value, 2)

    won_item = None
    returned_items = []
    coins_added = 0.0
    recorded = []

    if total_win_value > 0:
        # ищем предмет под сумму (без учёта редкости — просто ближайший по цене)
        affordable = [it for it in ITEMS_DB.values() if it["price"] <= total_win_value]
        if affordable:
            best_item = max(affordable, key=lambda x: x["price"])
            mut = roll_mutation(best_item["rarity"])
            info = item_with_traits(best_item["id"], mut, [])
            while info["price"] > total_win_value and mut != "normal":
                mut = "normal"
                info = item_with_traits(best_item["id"], mut, [])
            inv_id = db["next_inv_id"]
            db["next_inv_id"] += 1
            user["inventory"].append({"inv_id": inv_id, "item_id": best_item["id"], "mutation": mut, "traits": []})
            won_item = info
            recorded.append(info)
            remainder = round(total_win_value - info["price"], 2)
            if remainder > 0:
                user["balance"] = round(user["balance"] + remainder, 2)
                coins_added = remainder
        else:
            user["balance"] = round(user["balance"] + total_win_value, 2)
            coins_added = total_win_value

    if recorded:
        record_daily_drop(db, req.user_id, recorded, "pickaxe")

    github_save_db(db, sha)

    return {
        "tier": tier,
        "tier_name": pick_cfg["name"],
        "pickaxe_cost": pick_cost,
        "depth": depth,
        "multiplier": mult,
        "total_bet": total_bet,
        "ores_total_value": round(ores_total_value, 2),
        "ores": ores_summary,
        "events": events_log,
        "total_win": total_win_value,
        "won_item": won_item,
        "coins_added": coins_added,
        "returned_items": returned_items,
    }
@app.post("/api/keno/play")
def keno_play(req: KenoReq):
    if req.coins_bet < 0:
        raise HTTPException(status_code=400, detail="Некорректная ставка монет")
    picked = list(dict.fromkeys(int(x) for x in (req.picked or []) if 1 <= int(x) <= KENO_MAX))
    if not (1 <= len(picked) <= 10):
        raise HTTPException(status_code=400, detail="Выберите от 1 до 10 чисел (1..80)")

    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.user_id)

    if req.coins_bet > user["balance"]:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    inv_map = {e["inv_id"]: e for e in user["inventory"] if not e.get("locked")}
    bet_items = []
    items_value = 0.0
    for inv_id in req.inv_ids or []:
        if inv_id not in inv_map or inv_map[inv_id]["item_id"] not in ITEMS_DB:
            raise HTTPException(status_code=400, detail="Ошибка проверки предметов инвентаря")
        e = inv_map[inv_id]
        info = item_with_traits(e["item_id"], e.get("mutation", "normal"), e.get("traits", []))
        items_value += info["price"]
        bet_items.append({"inv_id": inv_id, "item_id": e["item_id"], "mutation": e.get("mutation", "normal"), "traits": e.get("traits", [])})

    total_bet = round(items_value + req.coins_bet, 2)
    if total_bet <= 0:
        raise HTTPException(status_code=400, detail="Сделайте ставку монетами или вещами")

    user["balance"] = round(user["balance"] - req.coins_bet, 2)
    selected_set = set(req.inv_ids or [])
    user["inventory"] = [e for e in user["inventory"] if e["inv_id"] not in selected_set]

    drawn = sorted(random.sample(range(1, KENO_MAX + 1), KENO_DRAW))
    drawn_set = set(drawn)
    matches = sum(1 for n in picked if n in drawn_set)
    multiplier = keno_payout(len(picked), matches)

    total_win_value = 0.0
    won_item = None
    returned_items = []
    coins_added = 0.0
    recorded = []

    if multiplier > 0:
        total_win_value = round(total_bet * multiplier, 2)
        won_item, returned_items, coins_added, recorded = _payout_like_crash(
            db, user, total_win_value, bet_items, items_value
        )
        if recorded:
            record_daily_drop(db, req.user_id, recorded, "keno")

    github_save_db(db, sha)
    return {
        "picked": sorted(picked),
        "drawn": drawn,
        "matches": matches,
        "picked_count": len(picked),
        "multiplier": multiplier,
        "win": multiplier > 0,
        "total_bet": total_bet,
        "total_win": total_win_value,
        "won_item": won_item,
        "returned_items": returned_items,
        "coins_added": coins_added,
    }# ...
@app.get("/api/admin/users")
def admin_users(admin_id: str):
    if not _is_admin(admin_id):
        raise HTTPException(status_code=403, detail="Нет доступа")
    db, sha = github_load_db()
    db = normalize_db(db)
    out = []
    for uid, u in db["users"].items():
        inv_val = 0.0
        for e in u.get("inventory", []):
            try:
                inv_val += item_with_traits(e["item_id"], e.get("mutation", "normal"), e.get("traits", []))["price"]
            except Exception:
                pass
        out.append({
            "user_id": uid,
            "username": u.get("username", ""),
            "first_name": u.get("first_name", ""),
            "balance": round(u.get("balance", 0), 2),
            "inv_count": len(u.get("inventory", [])),
            "inv_value": round(inv_val, 2),
            "online": is_online(u),
        })
    return {"users": out}


@app.post("/api/admin/promo/create")
def admin_promo_create(req: AdminPromoCreateReq):
    if not _is_admin(req.admin_id):
        raise HTTPException(status_code=403, detail="Нет доступа")
    code = (req.code or "").strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Пустой код")
    if req.type not in ("coins", "item"):
        raise HTTPException(status_code=400, detail="type: coins | item")
    db, sha = github_load_db()
    db = normalize_db(db)
    promos = db.setdefault("promocodes", {})
    if code in promos:
        raise HTTPException(status_code=400, detail="Такой промокод уже есть")
    entry = {"stock": max(1, int(req.stock or 1)), "type": req.type, "used_by": []}
    if req.type == "coins":
        entry["amount"] = float(req.amount or 0)
    else:
        if req.item_id not in ITEMS_DB:
            raise HTTPException(status_code=400, detail="item_id не найден")
        entry["item_id"] = int(req.item_id)
    promos[code] = entry
    github_save_db(db, sha)
    return {"ok": True, "code": code}


@app.post("/api/admin/promo/delete")
def admin_promo_delete(req: AdminPromoDeleteReq):
    if not _is_admin(req.admin_id):
        raise HTTPException(status_code=403, detail="Нет доступа")
    code = (req.code or "").strip().upper()
    db, sha = github_load_db()
    db = normalize_db(db)
    promos = db.setdefault("promocodes", {})
    if code not in promos:
        raise HTTPException(status_code=400, detail="Промокод не найден")
    promos.pop(code, None)
    github_save_db(db, sha)
    return {"ok": True}


@app.post("/api/admin/balance")
def admin_balance(req: AdminBalanceReq):
    if not _is_admin(req.admin_id):
        raise HTTPException(status_code=403, detail="Нет доступа")
    if req.action not in ("add", "sub"):
        raise HTTPException(status_code=400, detail="action: add | sub")
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="amount > 0")
    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.target_user_id)
    if req.action == "add":
        user["balance"] = round(user["balance"] + req.amount, 2)
    else:
        user["balance"] = round(max(0.0, user["balance"] - req.amount), 2)
    github_save_db(db, sha)
    return {"ok": True, "new_balance": user["balance"]}


@app.post("/api/admin/give_item")
def admin_give_item(req: AdminGiveItemReq):
    if not _is_admin(req.admin_id):
        raise HTTPException(status_code=403, detail="Нет доступа")
    if req.item_id not in ITEMS_DB:
        raise HTTPException(status_code=400, detail="item_id не найден")
    mut = req.mutation if (req.mutation in MUTATIONS) else "normal"
    if not rarity_allows_mutation(ITEMS_DB[req.item_id]["rarity"]):
        mut = "normal"
    traits = [k for k in (req.traits or []) if k in TRAITS_DB]
    db, sha = github_load_db()
    db = normalize_db(db)
    user = ensure_user(db, req.target_user_id)
    inv_id = db["next_inv_id"]
    db["next_inv_id"] += 1
    user["inventory"].append({"inv_id": inv_id, "item_id": req.item_id, "mutation": mut, "traits": traits})
    info = item_with_traits(req.item_id, mut, traits)
    record_daily_drop(db, req.target_user_id, [info], "admin_give")
    github_save_db(db, sha)
    return {"ok": True, "inv_id": inv_id, "item": info}


@app.post("/api/admin/event/start")
def admin_event_start(req: AdminEventStartReq):
    if not _is_admin(req.admin_id):
        raise HTTPException(status_code=403, detail="Нет доступа")
    if req.event_type not in ("trait", "mutation"):
        raise HTTPException(status_code=400, detail="event_type: trait | mutation")
    if req.event_type == "trait":
        if req.trait_key not in TRAITS_DB:
            raise HTTPException(status_code=400, detail="trait_key не найден")
    else:
        if req.mutation_key not in MUTATIONS or req.mutation_key == "normal":
            raise HTTPException(status_code=400, detail="mutation_key не найден")
    tick = max(10, min(int(req.tick_seconds or 45), 3600))
    chance = max(0.1, min(float(req.chance_percent or 5.0), 100.0))
    duration = max(30, min(int(req.duration_seconds or 600), 24 * 3600))
    db, sha = github_load_db()
    db = normalize_db(db)
    events = db.setdefault("events", {})
    eid = str(int(time.time() * 1000)) + str(random.randint(1000, 9999))
    events[eid] = {
        "event_type": req.event_type,
        "trait_key": req.trait_key,
        "mutation_key": req.mutation_key,
        "tick_seconds": tick,
        "chance_percent": chance,
        "until": int(time.time()) + duration,
        "started_at": int(time.time()),
    }
    github_save_db(db, sha)
    return {"ok": True, "event_id": eid}


@app.post("/api/admin/event/stop")
def admin_event_stop(req: AdminEventStopReq):
    if not _is_admin(req.admin_id):
        raise HTTPException(status_code=403, detail="Нет доступа")
    db, sha = github_load_db()
    db = normalize_db(db)
    events = db.setdefault("events", {})
    events.pop(req.event_id, None)
    github_save_db(db, sha)
    return {"ok": True}


@app.post("/api/admin/luck/start")
def admin_luck_start(req: AdminLuckStartReq):
    if not _is_admin(req.admin_id):
        raise HTTPException(status_code=403, detail="Нет доступа")
    if req.multiplier not in (2, 4):
        raise HTTPException(status_code=400, detail="multiplier: 2 | 4")
    duration = max(30, min(int(req.duration_seconds or 600), 24 * 3600))
    db, sha = github_load_db()
    db = normalize_db(db)
    db["luck_event"] = {"multiplier": int(req.multiplier), "until": int(time.time()) + duration}
    github_save_db(db, sha)
    return {"ok": True}


@app.post("/api/admin/luck/stop")
def admin_luck_stop(req: AdminLuckStopReq):
    if not _is_admin(req.admin_id):
        raise HTTPException(status_code=403, detail="Нет доступа")
    db, sha = github_load_db()
    db = normalize_db(db)
    db["luck_event"] = {"multiplier": 0, "until": 0}
    github_save_db(db, sha)
    return {"ok": True}


@app.post("/api/admin/global_message")
def admin_global_message(req: AdminGlobalMessageReq):
    if not _is_admin(req.admin_id):
        raise HTTPException(status_code=403, detail="Нет доступа")
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Текст пустой")
    if len(text) > 500:
        raise HTTPException(status_code=400, detail="Текст слишком длинный (макс. 500)")
    duration = max(5, min(int(req.duration_seconds or 60), 3600))
    db, sha = github_load_db()
    db = normalize_db(db)
    db["global_message"] = {"text": text, "until": int(time.time()) + duration}
    github_save_db(db, sha)
    return {"ok": True}


@app.get("/api/daily_drops")
def get_daily_drops():
    db, sha = github_load_db()
    db = normalize_db(db)
    return _public_daily_drops(db)


# ---------- ЭТАП 6: ТРЕЙДЫ ----------
def _resolve_target(db, target: str) -> str:
    """Превращает @username / username / user_id в user_id. Бросает 404, если не найден."""
    t = (target or "").strip()
    if not t:
        raise HTTPException(status_code=400, detail="Укажите @username или user_id")
    if t.startswith("@"):
        t = t[1:]
    # сначала ищем по user_id
    if t in db.get("users", {}):
        return t
    # ищем по username (регистронезависимо)
    for uid, u in db.get("users", {}).items():
        if (u.get("username") or "").lower() == t.lower():
            return uid
    raise HTTPException(status_code=404, detail="Игрок не найден")


@app.get("/api/trade/find_user")
def trade_find_user(q: str):
    q = (q or "").strip()
    if q.startswith("@"):
        q = q[1:]
    if not q:
        raise HTTPException(status_code=400, detail="Введите @username или ID")
    db, sha = github_load_db()
    db = normalize_db(db)
    matches = []
    for uid, u in db.get("users", {}).items():
        uname = (u.get("username") or "")
        if uid == q or uname.lower() == q.lower():
            matches.append({
                "user_id": uid,
                "username": uname,
                "first_name": u.get("first_name", ""),
                "online": is_online(u),
            })
    if not matches:
        raise HTTPException(status_code=404, detail="Игрок не найден")
    return {"matches": matches}


@app.get("/api/trade/history/{user_id}")
def trade_history(user_id: str):
    db, sha = github_load_db()
    db = normalize_db(db)
    out = []
    for t in reversed(db.get("trades", [])):
        if t.get("from_user_id") == user_id or t.get("to_user_id") == user_id:
            out.append(t)
        if len(out) >= 20:
            break
    return {"trades": out}


@app.post("/api/trade/send")
def trade_send(req: TradeSendReq):
    if not req.from_user_id:
        raise HTTPException(status_code=400, detail="Некорректный user_id")
    if req.coins < 0:
        raise HTTPException(status_code=400, detail="coins < 0")
    if len(req.inv_ids or []) > TRADE_MAX_ITEMS:
        raise HTTPException(status_code=400, detail=f"Максимум {TRADE_MAX_ITEMS} предметов за трейд")

    db, sha = github_load_db()
    db = normalize_db(db)

    from_id = req.from_user_id
    if from_id not in db["users"]:
        raise HTTPException(status_code=400, detail="Отправитель не найден")
    from_user = ensure_user(db, from_id)
    from_user["last_seen"] = int(time.time())

    target_id = _resolve_target(db, req.target)
    if target_id == from_id:
        raise HTTPException(status_code=400, detail="Нельзя трейдить самому себе")
    to_user = ensure_user(db, target_id)
    if not is_online(to_user):
        raise HTTPException(status_code=400, detail="Получатель не в сети (заходил > 5 мин назад)")

    # собираем предметы
    from_inv = {e["inv_id"]: e for e in from_user["inventory"]}
    picked_entries = []
    items_value = 0.0
    for iid in req.inv_ids or []:
        e = from_inv.get(iid)
        if not e:
            raise HTTPException(status_code=400, detail=f"Предмет {iid} не найден у вас")
        if e.get("locked"):
            raise HTTPException(status_code=400, detail=f"Предмет {iid} заблокирован (вывод)")
        info = item_with_traits(e["item_id"], e.get("mutation", "normal"), e.get("traits", []))
        items_value += info["price"]
        picked_entries.append(e)

    coins = round(float(req.coins or 0), 2)

    # комиссия 15% с монет и с рыночной стоимости вещей
    commission_from_coins = round(coins * TRADE_COMMISSION, 2)
    commission_from_items = round(items_value * TRADE_COMMISSION, 2)
    total_commission = round(commission_from_coins + commission_from_items, 2)

    # с отправителя списываем: coins (полные) + total_commission
    if from_user["balance"] < coins + total_commission:
        raise HTTPException(
            status_code=400,
            detail=f"Недостаточно монет с учётом комиссии {total_commission} 💰 (баланс {from_user['balance']:.2f})"
        )

    # перевод
    from_user["balance"] = round(from_user["balance"] - coins - total_commission, 2)
    to_user["balance"] = round(to_user["balance"] + (coins - commission_from_coins), 2)

    # перенос вещей
    moved = []
    for e in picked_entries:
        from_user["inventory"] = [x for x in from_user["inventory"] if x["inv_id"] != e["inv_id"]]
        to_user["inventory"].append(e)
        moved.append({
            "inv_id": e["inv_id"],
            "item_id": e["item_id"],
            "mutation": e.get("mutation", "normal"),
            "traits": e.get("traits", []),
            "price": item_with_traits(e["item_id"], e.get("mutation", "normal"), e.get("traits", []))["price"],
            "name": ITEMS_DB[e["item_id"]]["name"],
        })

    record = {
        "ts": int(time.time()),
        "from_user_id": from_id,
        "from_username": from_user.get("username", ""),
        "to_user_id": target_id,
        "to_username": to_user.get("username", ""),
        "coins_sent": coins,
        "coins_received": round(coins - commission_from_coins, 2),
        "items_value": round(items_value, 2),
        "commission": total_commission,
        "items": moved,
    }
    db.setdefault("trades", []).append(record)
    if len(db["trades"]) > 500:
        db["trades"] = db["trades"][-500:]

    github_save_db(db, sha)

    # уведомления через бота (если есть)
    if BOT_TOKEN:
        try:
            uname_to = to_user.get("username") or to_user.get("first_name") or target_id
            send_tg_message(target_id,
                f"🤝 Вам трейд от {from_user.get('username') or from_id}:\n"
                f"• монеты: {record['coins_received']} 💰 (комиссия {commission_from_coins} 💰)\n"
                f"• предметов: {len(moved)}\n"
                f"• комиссия с предметов: {commission_from_items} 💰 (списана с отправителя)")
        except Exception:
            pass

    return {
        "ok": True,
        "to_user_id": target_id,
        "coins_received": record["coins_received"],
        "commission_from_coins": commission_from_coins,
        "commission_from_items": commission_from_items,
        "total_commission": total_commission,
        "items_moved": len(moved),
    }


# ---------- Фоновые ивенты ----------
def _events_loop():
    last_tick = {}
    while True:
        try:
            time.sleep(10)
            db, sha = github_load_db()
            db = normalize_db(db)
            now = int(time.time())
            events = db.get("events") or {}
            changed = False
            for eid, ev in list(events.items()):
                if int(ev.get("until", 0)) <= now:
                    events.pop(eid, None)
                    last_tick.pop(eid, None)
                    changed = True
                    continue
                tick_sec = int(ev.get("tick_seconds", 45))
                prev = last_tick.get(eid, int(ev.get("started_at", now)))
                if now - prev < tick_sec:
                    continue
                last_tick[eid] = now
                chance = float(ev.get("chance_percent", 5.0))
                if random.uniform(0, 100) > chance:
                    continue
                candidates = []
                for uid, u in db.get("users", {}).items():
                    for e in u.get("inventory", []):
                        if e.get("locked"):
                            continue
                        if ev["event_type"] == "trait":
                            if ev["trait_key"] not in (e.get("traits") or []):
                                candidates.append((uid, e))
                        else:
                            item_info = ITEMS_DB.get(e.get("item_id"))
                            if not item_info:
                                continue
                            if not rarity_allows_mutation(item_info["rarity"]):
                                continue
                            cur_mult = mutation_mult(e.get("mutation", "normal"))
                            new_mult = mutation_mult(ev["mutation_key"])
                            if new_mult > cur_mult:
                                candidates.append((uid, e))
                if not candidates:
                    continue
                uid, entry = random.choice(candidates)
                if ev["event_type"] == "trait":
                    entry.setdefault("traits", [])
                    if ev["trait_key"] not in entry["traits"]:
                        entry["traits"].append(ev["trait_key"])
                        changed = True
                else:
                    entry["mutation"] = ev["mutation_key"]
                    changed = True
            if changed:
                github_save_db(db, sha)
        except Exception:
            time.sleep(5)


if BOT_TOKEN or True:
    threading.Thread(target=_events_loop, daemon=True).start()