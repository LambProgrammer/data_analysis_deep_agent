# ==========================================
# 本文件用于启动项目的Worker服务
# ==========================================


import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.core.queue import app as procrastinate_app
from app.utils.db import init_db, close_db
import app.services.analysis_service  # ← 关键：导入任务模块，触发注册

async def main():
    print("正在打开数据库连接...")
    await procrastinate_app.open_async()
    # 初始化业务数据库连接池
    await init_db()
    print("🚀 Worker 启动中...")
    try:
        await procrastinate_app.run_worker_async()
    finally:
        await close_db()
        await procrastinate_app.close_async()

asyncio.run(main())