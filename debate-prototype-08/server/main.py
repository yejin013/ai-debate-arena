import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 절대 경로 임포트로 수정
from routers import workflow

# 데이터베이스 초기화를 위한 임포트 추가
from db.database import Base, engine
from server.routers import history

# 시작 시 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)
# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Debate Arena API",
    description="AI Debate Arena 서비스를 위한 API",
    version="0.1.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 구체적인 도메인으로 변경
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 포함
app.include_router(history.router)
app.include_router(workflow.router)


# 상태 확인용 루트 엔드포인트
@app.get("/")
async def root():
    return {"status": "active", "message": "Debate Arena API 서버가 실행 중입니다."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
