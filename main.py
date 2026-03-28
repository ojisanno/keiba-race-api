from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Flutter からアクセスできるように CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ★ 今日のレース一覧（まずは固定データ）
@app.get("/races/today")
def get_today_races():
    races = [
        {"race": 1, "time": "10:00"},
        {"race": 2, "time": "10:30"},
        {"race": 3, "time": "11:00"},
        {"race": 4, "time": "11:30"},
        {"race": 5, "time": "12:00"},
        {"race": 6, "time": "12:30"},
        {"race": 7, "time": "13:00"},
        {"race": 8, "time": "13:30"},
        {"race": 9, "time": "14:00"},
        {"race": 10, "time": "14:30"},
        {"race": 11, "time": "15:00"},
        {"race": 12, "time": "15:30"},
    ]
    return {"races": races}
