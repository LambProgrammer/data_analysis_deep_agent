# ==========================================
# 本文件用于测试procrastinate的PsycopgConnector异步连接
# 根目录终端执行：python test_async_conn.py
# ==========================================


import asyncio
import selectors  # 新增

from procrastinate import App, PsycopgConnector

from config import config


async def main():
    app = App(connector=PsycopgConnector(conninfo=config.DATABASE_URL))
    await app.open_async()
    print("✅ 异步连接成功")
    await app.close_async()

# 关键：在 Windows 上强制使用 SelectorEventLoop
asyncio.run(main(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))




