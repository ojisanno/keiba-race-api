from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
from bs4 import BeautifulSoup
from datetime import datetime

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
# 開催場コード（JRA）
# ============================================
COURSE_CODE = {
    "札幌": "01",
    "函館": "02",
    "福島": "03",
    "新潟": "04",
    "東京": "05",
    "中山": "06",
    "中京": "07",
    "京都": "08",
    "阪神": "09",
    "小倉": "10",
}

# ============================================
# レース名（固定）
# ============================================
RACE_NAMES = {
    1: "2歳未勝利",
    2: "3歳未勝利",
    3: "障害オープン",
    4: "1勝クラス",
    5: "2勝クラス",
    6: "3勝クラス",
    7: "オープン",
    8: "特別戦",
    9: "G3",
    10: "G2",
    11: "G1",
    12: "最終レース",
}

# ============================================
# 今日の日付（自動）
# ============================================
def get_today_str():
    return datetime.now().strftime("%Y%m%d")

# ============================================
# raceId を生成する関数
# ============================================
def make_race_id(date_str: str, course: str, race_number: int):
    course_code = COURSE_CODE.get(course, "00")
    return f"{date_str}{course_code}{race_number:02d}"

# ============================================
# 今日のレース一覧（自動日付＋raceId付き）
# ============================================
@app.get("/races/today")
def get_today_races(course: str):
    print("今日のレース取得:", course)

    today = get_today_str()

    races = []
    for i in range(1, 13):
        race_id = make_race_id(today, course, i)
        races.append({
            "raceNumber": i,
            "name": RACE_NAMES[i],
            "raceId": race_id,
        })

    return {"races": races}

# ============================================
# 過去レース一覧（date を指定）
# ============================================
@app.get("/races/past")
def get_past_races(course: str, date: str):
    print("過去レース取得:", course, date)

    races = []
    for i in range(1, 13):
        race_id = make_race_id(date, course, i)
        races.append({
            "raceNumber": i,
            "name": RACE_NAMES[i],
            "raceId": race_id,
        })

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
# 歪み判定API
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
