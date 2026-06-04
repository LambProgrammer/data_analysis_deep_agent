"""
FastAPI 应用入口模块。app/main.py
- 创建 FastAPI 实例
- 管理应用生命周期（启动 / 关闭）
- 注册各个业务路由
- 提供根路径健康检查
""" 

from contextlib import asynccontextmanager          # 用于将异步生成器包装为上下文管理器
from fastapi import FastAPI
from app.routes.analysis import router as analysis_router  # 导入分析模块的路由
from app.core.queue import app as procrastinate_app
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import AsyncGenerator
from app.utils.db import init_db, close_db


# ===========================
# 应用生命周期管理
# ===========================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI 应用生命周期管理。

    启动阶段（yield 之前）：
    1. 执行自定义的初始化操作（如设置状态标记）。
    2. 打开 Procrastinate 的数据库连接池，确保后续任务提交和 Worker 能正常工作。

    关闭阶段（yield 之后）：
    1. 关闭 Procrastinate 连接池，释放数据库连接资源。
    2. 其他清理操作可在此添加。
    """
    
    # ========== 启动阶段 ==========
    # 设置启动完成标志（可根据需要保留）
    print("🚀 Lifespan 启动，正在打开 Procrastinate 连接...")
    # app.state.startup_complete = True

    await init_db()
    print("✅ 数据库业务连接池已初始化")

    # 初始化 Procrastinate 连接池
    # 这会让我们的 Web 服务能够将任务成功写入 PostgreSQL 队列
    try:
        await procrastinate_app.open_async()
        print("✅ Procrastinate 连接已打开")
    except Exception as e:
        print(f"❌ 打开连接失败: {e}")
        raise
      
    # yield 交出控制权，FastAPI 开始接收请求
    yield
    
    # ========== 关闭阶段 ==========
    await close_db()
    print("✅ 数据库业务连接池已关闭")
    # 优雅关闭 Procrastinate 连接池
    print("🛑 Lifespan 关闭，正在关闭连接...")
    await procrastinate_app.close_async()
    print("✅ 连接已关闭")
    # 其他资源清理代码可以加在这里






# ===========================
# 创建 FastAPI 应用实例
# ===========================

app = FastAPI(
    title="Data Analysis Deep Agent",
    description="A data analysis deep agent powered by LLM",
    version="0.1.0",
    lifespan=lifespan           # 挂载生命周期
)





# ===========================
# 注册业务路由模块
# ===========================

# 将 analysis 路由模块挂载到 /analysis 路径下
# 路由中定义的所有端点都会自动加上 /analysis 前缀
# tags 参数让 OpenAPI 文档按 "Analysis" 分组显示这些接口
app.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])
app.mount("/", StaticFiles(directory="static", html=True), name="static")






# ===========================
# 根路径 - 健康检查 / 服务入口
# ===========================

@app.get("/")
async def root():
    """
    根路径端点，常用于：
    - 快速验证服务是否正常运行（健康检查）
    - 提供简单的服务信息或欢迎页面
    - 负载均衡器、容器编排平台（如 Kubernetes）可通过此端点进行存活探测
    """
    return {"message": "Deep Data Analysis Agent API"}




app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发阶段允许所有源，生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


