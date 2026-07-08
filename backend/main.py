from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import analysis, budget, ai, notify, report, archive, budget_batch
from models import init_db
import os
import logging

# 统一日志配置：路由层用 logging.getLogger(__name__) 即可输出到控制台，
# 500 异常用 logger.exception() 记完整堆栈，避免把内部细节经 JSONResponse 泄露给前端
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(title="在建工程分析系统", version="1.0.0")

# 初始化数据库
init_db()

# 允许前端跨域访问（通过环境变量 CORS_ORIGINS 配置，逗号分隔，默认 localhost:5173）
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(analysis.router, prefix="/api/zaigong", tags=["在建工程"])
app.include_router(budget.router, prefix="/api/budget", tags=["预算分析"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI分析"])
app.include_router(notify.router, prefix="/api/notify", tags=["通知"])
app.include_router(report.router, prefix="/api/report", tags=["月报"])
app.include_router(archive.router, prefix="/api/archive", tags=["数据档案"])
app.include_router(budget_batch.router, prefix="/api/budget-batch", tags=["投资批次"])

@app.get("/")
async def root():
    return {"message": "在建工程分析系统 API", "version": "1.0.0"}
