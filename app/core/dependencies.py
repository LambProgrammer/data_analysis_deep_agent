"""
FastAPI 依赖注入模块。

本模块使用 FastAPI 的依赖注入系统，集中管理应用核心组件的创建和缓存。
所有依赖工厂函数均使用 @lru_cache() 装饰，确保返回的实例在应用生命周期内
只创建一次，避免重复初始化重量级资源（如 LocalShellBackend、Agent）。
"""

import asyncio
import os
import modal
from langchain_modal import ModalSandbox
from deepagents.backends import LocalShellBackend     # Agent 的本地 Shell 后端（沙箱执行环境）
from deepagents import create_deep_agent              # 工厂函数：创建具备工具调用能力的 Agent
from langgraph.checkpoint.memory import InMemorySaver # LangGraph 的内存检查点存储器（用于多轮对话状态持久化）
from llm_provider import get_deepseek_llm                 # 外部定义的 DeepSeek LLM 实例
from pathlib import Path
from functools import lru_cache                       # 缓存函数调用结果，实现单例模式
from contextlib import asynccontextmanager          # 用于创建异步上下文管理器
from app.core.modal_app import APP_NAME



# 计算项目根目录的绝对路径
# __file__ 是当前文件的路径，例如 /project/app/core/dependencies.py
# .resolve() 获得绝对路径
# .parent 获取父目录（第一次得到 core/，第二次得到 app/，第三次得到项目根目录）
# 因此 _root 指向项目根目录（与 main.py 同级的目录）
_root = Path(__file__).resolve().parent.parent.parent  # 项目根目录

# skills 目录的绝对路径
SKILLS_DIR = _root / "skills"



@lru_cache()
def get_checkpointer():
    """
    创建并缓存 Agent 的内存检查点存储器。

    LangGraph 使用检查点（Checkpoint）来保存对话状态和已执行的操作步骤。
    InMemorySaver 将状态保存在内存中，适用于单个服务实例的场景。

    注意：
    - 服务重启后内存状态会丢失，生产环境可替换为持久化存储器（如 SqliteSaver）。
    - 如果不需要多轮对话状态管理，也可以不注入 Checkpointer。

    返回：
        InMemorySaver 实例，该实例会被缓存，多个 Agent 调用共享同一存储。
    """
    return InMemorySaver()



# ========== 任务级沙箱后端 ==========
@asynccontextmanager
async def task_sandbox_agent():
    """
    为单个分析任务创建一个独立的 Modal 沙箱和 Agent。

    使用异步上下文管理器 (async with) 自动管理沙箱的创建和销毁，
    确保任务执行完毕后立即释放资源，并完全隔离不同任务的执行环境。

    Yields:
        Agent 实例，可直接用于 agent.ainvoke() 等操作。

    用法示例:
        async with task_sandbox_agent() as agent:
            result = await agent.ainvoke(...)
    """
    
    # 1. 构建预装分析依赖的镜像
    image = (
        modal.Image.debian_slim()
        .pip_install("pandas", "matplotlib", "openpyxl")
    )

    # 2. 查找已部署的 Modal App（确保已执行 modal deploy app/core/modal_app.py）
    app = await modal.App.lookup.aio(APP_NAME)  

    # 3. 创建沙箱
    sandbox = await modal.Sandbox.create.aio(
        app=app,  
        image=image,
        timeout=600,      # 单个任务最长执行时间（秒）
        workdir="/data",
    )
    
        
    backend = ModalSandbox(sandbox=sandbox)
    checkpointer = get_checkpointer()
    
    # deep agent 的 skills 参数需要一个路径字符串列表，
    # 此处将 skills 目录的绝对路径作为唯一元素传入。
    skills = [str(SKILLS_DIR)]
    
    # 4. 创建 Agent
    agent = create_deep_agent(
        model=get_deepseek_llm(),
        backend=backend,
        checkpointer=checkpointer
    )

    try:
        yield sandbox, agent          # 将 Agent和sandbox 交给任务函数
    
    # 5. 无论任务成功还是失败，都确保销毁沙箱
    finally:
        await sandbox.terminate.aio()