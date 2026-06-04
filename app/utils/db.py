"""
业务数据库操作模块（异步）。

本模块负责管理业务表 `tasks` 的所有读写操作，使用 asyncpg 异步驱动。

设计要点：
- 使用连接池（asyncpg.create_pool）复用数据库连接，避免每次操作都建立新连接
- 连接池在应用启动时由 init_db() 初始化，关闭时由 close_db() 回收
- 所有数据库操作均为异步函数，不会阻塞事件循环
- 调用方必须在调用本模块函数前先调用 await init_db()

使用示例：
    # 启动时
    await init_db()

    # 业务中
    await update_task_db(task_id="xxx", status="completed", summary="分析完成")
    task = await get_task_from_db("xxx")
"""


import asyncpg
from config import config


# 全局连接池对象，None 表示未初始化
# 使用模块级单例，整个应用共享一个连接池
_pool = None



async def init_db():
    """
    初始化业务数据库连接池。

    应在应用启动阶段（FastAPI lifespan 或 Worker main）调用一次。
    调用后 _pool 对象被赋值，后续所有函数可复用该池。

    参数说明：
        min_size=2  → 连接池至少保持 2 个空闲连接
        max_size=10 → 连接池最多允许 10 个连接（防止打爆数据库）
    """
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(config.DATABASE_URL, min_size=2, max_size=10)


async def close_db():
    """
    关闭业务数据库连接池。

    应在应用关闭阶段调用，确保所有连接被释放。
    """
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def update_task_db(task_id: str, status: str, summary=None, chart_path=None, chart_available=False, error=None):
    """
    插入或更新 tasks 表中的任务记录（异步）。

    使用 PostgreSQL 的 INSERT ... ON CONFLICT DO UPDATE 语法（UPSERT）：
    - 如果 task_id 不存在，插入新行
    - 如果 task_id 已存在，更新现有行

    参数：
        task_id         - 任务的唯一标识（UUID 字符串）
        status          - 任务状态：pending / running / completed / failed
        summary         - 分析结论文本（仅 completed 时有值）
        chart_path      - 图表文件的本地路径（仅 completed 且有图表时有值）
        chart_available  - 是否成功生成了图表
        error           - 错误信息（仅 failed 时有值）
    """
    if _pool is None:
        raise RuntimeError("数据库连接池未初始化，请先调用 init_db()")
    
    
    # 从连接池获取一个连接，async with 块结束后自动归还
    async with _pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO tasks (task_id, status, summary, chart_path, chart_available, error)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (task_id) DO UPDATE SET
                status = EXCLUDED.status,
                summary = EXCLUDED.summary,
                chart_path = EXCLUDED.chart_path,
                chart_available = EXCLUDED.chart_available,
                error = EXCLUDED.error,
                updated_at = NOW()
            """,
            task_id, status, summary, chart_path, chart_available, error
        )


async def get_task_from_db(task_id: str) -> dict | None:
    """
    根据 task_id 查询任务记录（异步）。

    返回：
        如果找到记录，返回包含任务信息的字典，键名与表列名一致
        如果未找到，返回 None
    """
    if _pool is None:
        raise RuntimeError("数据库连接池未初始化，请先调用 init_db()")
    
    async with _pool.acquire() as conn:
        # fetchrow 返回单行，无结果时返回 None
        row = await conn.fetchrow(
            """
            SELECT status, summary, chart_available, chart_path, error
            FROM tasks
            WHERE task_id = $1
            """,
            task_id
        )
        if row is None:
            return None
        
        # 将 asyncpg.Record 转换为普通字典，方便调用方使用 .get() 等方法
        return {
            "status": row["status"],
            "summary": row["summary"],
            "chart_available": row["chart_available"],
            "chart_path": row["chart_path"],
            "error": row["error"],
        }