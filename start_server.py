# ==========================================
# 本文件用于在项目开发、改造测试时，使用启动脚本运行uvicorn
# 这是因为在Windows系统环境下，uvicorn的cli指令对于异步任务的事件循环不好兼容
# ==========================================



import asyncio
import sys

import uvicorn

if __name__ == "__main__":
    # 1. 在 Windows 上强制使用 SelectorEventLoop
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        loop = asyncio.SelectorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.new_event_loop()

    # 2. 配置 Uvicorn，loop 参数设为 "asyncio"（不使用 uvloop）
    config = uvicorn.Config(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        loop="asyncio",
        # 开发阶段可以先关闭 reload，稳定后再加
        # reload=True,
    )
    server = uvicorn.Server(config)

    # 3. 用我们自己的事件循环运行服务器
    async def main():
        await server.serve()

    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
