# ==========================================
# 本文件用于测试Agent的backend运行环境是否成功运行在沙箱中
# 根目录终端执行：python test_agent_sandbox.py
# ==========================================


import asyncio
from app.core.dependencies import task_sandbox_agent

async def main():
    print("Testing task_sandbox_agent...")
    async with task_sandbox_agent() as (sandbox, agent):
        # 可以上传一个测试文件
        print("Agent ready, sandbox id:", sandbox.object_id)                # type: ignore
        result = await agent.ainvoke(                                       # type: ignore
            {"messages": [{"role": "user", "content": "用 Python 生成一个 1 到 10 的列表并打印"}]},
            config={"configurable": {"thread_id": "test-thread-1"}}  # type: ignore
        )
        print("Agent response:", result["messages"][-1].content)
    print("Sandbox terminated.")

asyncio.run(main())