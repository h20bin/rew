"""
산업현장 안전 모니터링 시스템 - 백엔드 메인
실행: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
API 문서: http://localhost:8000/docs
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.database import engine, Base
from app.api.routes.routes import router
from app.services.websocket_manager import manager

# ── DB 테이블 자동 생성 ────────────────────────────────────
Base.metadata.create_all(bind=engine)


def _create_default_admin():
    """서버 시작 시 admin 계정이 없으면 자동 생성 (admin / 1234)"""
    from app.core.database import SessionLocal
    from app.models.models import UserTable, UserRoleEnum
    from app.core.security import hash_password
    db = SessionLocal()
    try:
        if not db.query(UserTable).filter(UserTable.user_id == "admin").first():
            db.add(UserTable(
                user_id="admin",
                password=hash_password("1234"),
                name="관리자",
                role=UserRoleEnum.ADMIN,
            ))
            db.commit()
            print("✅ 기본 계정 생성 완료: admin / 1234")
    finally:
        db.close()

_create_default_admin()

# ── FastAPI 앱 ─────────────────────────────────────────────
app = FastAPI(
    title="산업현장 안전 모니터링 시스템 API",
    description="""
## 팀 F - 캡스톤디자인

### 주요 기능
- 🔐 사용자 인증 (JWT)
- 👷 작업자 관리
- 📷 카메라 관리
- ⚠️ 위험구역 설정 (가변)
- 🚨 위험 이벤트 저장 / 조회
- 🔔 경보 장치 제어 (LED / 부저)
- 📊 통계 분석
- 🔄 WebSocket 실시간 경보
    """,
    version="1.0.0",
)

# ── CORS 설정 ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 배포 시 실제 도메인으로 변경
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 이미지 정적 파일 서빙 ──────────────────────────────────
os.makedirs("./uploads/images", exist_ok=True)
app.mount("/images", StaticFiles(directory="./uploads/images"), name="images")

# ── 프론트엔드 서빙 (/ui) ──────────────────────────────────
os.makedirs("./frontend", exist_ok=True)
app.mount("/ui", StaticFiles(directory="./frontend", html=True), name="frontend")

# ── 라우터 등록 ────────────────────────────────────────────
app.include_router(router, prefix="/api/v1")


# ── WebSocket 실시간 경보 ──────────────────────────────────
@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    관제 대시보드 WebSocket 연결
    - 클라이언트(관제 화면)에서 연결 후 대기
    - 위험 이벤트 발생 시 서버가 자동으로 푸시
    """
    await manager.connect(websocket)
    try:
        while True:
            # 클라이언트 연결 유지 (ping)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ── 헬스체크 ───────────────────────────────────────────────
@app.get("/health", tags=["시스템"])
def health_check():
    return {"status": "ok", "service": "safety-monitoring-backend"}


@app.get("/", tags=["시스템"])
def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/ui/login.html")
