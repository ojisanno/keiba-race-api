from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")
def hello():
    return {"message": "クラウドでPythonが動いています"}

from fastapi import FastAPI, HTTPException
import httpx

@app.get("/odds/simple-distortion")
async def simple_distortion(race_id: str, before: int, after: int):
    # ダミーのオッズ取得関数
    async def fetch_odds(race_id: str, minutes_before: int):
        return {
            "horses": [
                {"number": 3, "name": "サンプルホース", "odds": 5.0, "pop": 5},
                {"number": 7, "name": "テストホース", "odds": 12.0, "pop": 8},
            ]
        }

    odds_before = await fetch_odds(race_id, before)
    odds_after = await fetch_odds(race_id, after)

    result = []
    for hb in odds_before["horses"]:
        ha = next((x for x in odds_after["horses"] if x["number"] == hb["number"]), None)
        if not ha:
            continue

        change_rate = (ha["odds"] - hb["odds"]) / hb["odds"]
        pop_change = hb["pop"] - ha["pop"]
        distortion_score = abs(change_rate) * 100 + abs(pop_change) * 10

        if distortion_score >= 40:
            label = "強い歪み"
        elif distortion_score >= 20:
            label = "やや歪み"
        else:
            label = "通常"

        result.append({
            "number": hb["number"],
            "name": hb["name"],
            "odds_before": hb["odds"],
            "odds_after": ha["odds"],
            "pop_before": hb["pop"],
            "pop_after": ha["pop"],
            "odds_change_rate": round(change_rate, 3),
            "pop_change": pop_change,
            "distortion_score": round(distortion_score, 1),
            "label": label
        })

    return {
        "race_id": race_id,
        "before_minutes": before,
        "after_minutes": after,
        "horses": result
    }
