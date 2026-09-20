from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from ultra_engine import UltraLottoEngine

app = FastAPI(
    title="AI 로또 번호 분석 시스템 API",
    description="논문 및 통계 필터링 기반 최적 로또 번호 추천 API",
    version="1.0.0"
)

# Flutter 앱(모바일) 통신 허용 설정 (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서버启动 시 고도화 엔진 로드
engine = UltraLottoEngine()

@app.get("/")
def read_root():
    return {"status": "online", "message": "Lotto AI Backend Server is running!"}

@app.get("/api/v1/recommend")
def get_lotto_recommendations(games: int = Query(default=5, ge=1, le=10)):
    """
    Flutter 앱에서 호출할 핵심 API:
    원하는 게임 수(1~10)를 전달받아 최우수 적합도 번호를 반환합니다.
    """
    recommendations = engine.generate_recommendations(count=games)
    return {
        "success": True,
        "requested_games": games,
        "recommendations": recommendations
    }