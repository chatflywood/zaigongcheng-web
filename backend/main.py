from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import analysis, budget, ai
from models import init_db

app = FastAPI(title="在建工程分析系统", version="1.0.0")

# 初始化数据库
init_db()

# 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(analysis.router, prefix="/api/zaigong", tags=["在建工程"])
app.include_router(budget.router, prefix="/api/budget", tags=["预算分析"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI分析"])

@app.get("/")
async def root():
    return {"message": "在建工程分析系统 API", "version": "1.0.0"}
