from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
from bs4 import BeautifulSoup

app = FastAPI()

# ============================================
# CORS（Flutter からアクセスできるように）
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# 今日のレース一覧（固定データ）
# ============================================
@app.get("/races/today")
def get_today_races(course: str):
    print("今日のレース取得:", course)

    races = [
        {"raceNumber": 1, "name": "2歳未勝利"},
        {"raceNumber": 2, "name": "3歳未勝利"},
        {"raceNumber": 3, "name": "障害オープン"},
        {"raceNumber": 4, "name": "1勝クラス"},
        {"raceNumber": 5, "name": "2勝クラス"},
        {"raceNumber": 6, "name": "3勝クラス"},
        {"raceNumber": 7, "name": "オープン"},
        {"raceNumber": 8, "name": "特別戦"},
        {"raceNumber": 9, "name": "G3"},
        {"raceNumber": 10, "name": "G2"},
        {"raceNumber": 11, "name": "G1"},
        {"raceNumber": 12, "name": "最終レース"},
    ]

    return {"races": races}

# ============================================
# 過去レース一覧（固定データ）
# ============================================
@app.get("/races/past")
def get_past_races(course: str):
    print("過去レース取得:", course)

    races = [
        {"raceNumber": 1, "name": "2歳未勝利"},
        {"raceNumber": 2, "name": "3歳未勝利"},
        {"raceNumber": 3, "name": "障害オープン"},
        {"raceNumber": 4, "name": "1勝クラス"},
        {"raceNumber": 5, "name": "2勝クラス"},
        {"raceNumber": 6, "name": "3勝クラス"},
        {"raceNumber": 7, "name": "オープン"},
        {"raceNumber": 8, "name": "特別戦"},
        {"raceNumber": 9, "name": "G3"},
        {"raceNumber": 10, "name": "G2"},
        {"raceNumber": 11, "name": "G1"},
        {"raceNumber": 12, "name": "最終レース"},
    ]

    return {"races": races}

# ============================================
# 本物のオッズ取得（netkeiba スクレイピング）
# ============================================
async def fetch_odds(race_id: str):
    url = f"https://race.netkeiba.com/race/result.html?race_id={race_id}"

    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10.0)
        r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")

    horses = []
    rows = soup.select(".RaceTableArea .RaceTable01 tr")

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 10:
            continue

        try:
            number = int(cols[1].text.strip())
            name = cols[3].text.strip()
            odds_tan = float(cols[5].text.strip())
            pop = int(cols[6].text.strip())

            fuku_text = cols[7].text.strip()
            if "-" in fuku_text:
                fuku_min, fuku_max = fuku_text.split("-")
                fuku_min = float(fuku_min.strip())
                fuku_max = float(fuku_max.strip())
            else:
                fuku_min = fuku_max = float(fuku_text)

        except:
            continue

        horses.append({
            "number": number,
            "name": name,
            "odds_tan": odds_tan,
            "odds_fuku_min": fuku_min,
            "odds_fuku_max": fuku_max,
            "pop": pop
        })

    return {"horses": horses}

# ============================================
# 歪み判定API（本物のオッズ取得版）
# ============================================
def get_color(score: float):
    if score >= 60:
        return "#FF4D4D"
    elif score >= 30:
        return "#FFC93C"
    else:
        return "#4DA3FF"

@app.get("/odds/simple-distortion")
async def simple_distortion(race_id: str, before: int, after: int):
    odds_before = await fetch_odds(race_id)
    odds_after = await fetch_odds(race_id)

    result = []

    for hb in odds_before["horses"]:
        ha = next((x for x in odds_after["horses"] if x["number"] == hb["number"]), None)
        if not ha:
            continue

        tan_rate = (ha["odds_tan"] - hb["odds_tan"]) / hb["odds_tan"]

        before_fuku = (hb["odds_fuku_min"] + hb["odds_fuku_max"]) / 2
        after_fuku  = (ha["odds_fuku_min"] + ha["odds_fuku_max"]) / 2
        fuku_rate = (after_fuku - before_fuku) / before_fuku

        pop_change = ha["pop"] - hb["pop"]

        score = abs(tan_rate) * 100 + abs(fuku_rate) * 50 + abs(pop_change) * 10

        if score >= 60:
            label = "強い歪み"
        elif score >= 30:
            label = "やや歪み"
        else:
            label = "通常"

        color = get_color(score)

        result.append({
            "number": hb["number"],
            "name": hb["name"],
            "tan_before": hb["odds_tan"],
            "tan_after": ha["odds_tan"],
            "fuku_before": before_fuku,
            "fuku_after": after_fuku,
            "pop_before": hb["pop"],
            "pop_after": ha["pop"],
            "tan_rate": round(tan_rate, 3),
            "fuku_rate": round(fuku_rate, 3),
            "pop_change": pop_change,
            "score": round(score, 1),
            "label": label,
            "color": color
        })

    return {
        "race_id": race_id,
        "before_minutes": before,
        "after_minutes": after,
        "horses": result
    }

# ============================================
# 動作確認用
# ============================================
@app.get("/hello")
async def hello():
    return {"message": "クラウドでPythonが動いています"}
