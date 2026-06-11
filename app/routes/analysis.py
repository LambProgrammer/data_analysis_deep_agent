"""
分析业务路由模块。

本模块定义了与数据分析相关的 API 端点：
- POST /upload : 上传数据文件，创建后台分析任务。
- GET /{task_id} : 查询任务状态或获取分析结果。
- GET /{task_id}/chart : 下载分析生成的图表图片。

上传接口：保存文件 → 调用 procrastinate_app.defer(run_analysis_task, file_path=...)，
获取 job_id → 返回给前端

状态查询接口：使用 Procrastinate 的 JobManager 查询 job 状态，映射字段

图表接口：同样从 job result 获取 chart_path
"""

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.schemas.analysis import AnalysisResponse, AnalysisResult
from app.services.analysis_service import run_analysis_task  # 导入只是为了类型，实际由 defer 调用
from app.utils.db import get_task_from_db, update_task_db

# 创建 APIRouter 实例，后续所有分析相关的端点都注册在这个 router 上
# main.py 通过 app.include_router(router, prefix="/analysis") 挂载整个子路由
router = APIRouter()


# ===========================
# 任务状态存储（内存）
# ===========================
# 🔴 重要提示：这是一个简化的原型方案，只适用于单进程开发和调试。
# 生产环境请务必替换为 Redis、PostgreSQL 等可持久化存储，否则：
# 1. 服务重启后所有任务状态丢失
# 2. 多副本部署时任务无法共享
# task_store: dict[str, dict] = {}


# ===========================
# 上传文件存储目录
# ===========================
# 根据当前代码文件位置推导项目根目录
# 推导项目根：analysis.py → routes → app → 项目根
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = ROOT_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ===========================
# 端点 1：上传文件并触发分析
# ===========================
@router.post("/upload", response_model=AnalysisResponse)
async def upload_and_analyze(file: UploadFile = File(...)):
    # File(...) 表示该参数是必填的文件上传字段
    """
    上传 CSV 或 Excel 文件，启动后台分析任务。

    流程：
    1. 校验文件扩展名是否合法
    2. 将文件保存到服务器本地（或容器中）的 uploads 目录（使用 UUID 重命名）
    3. 通过Procrastinate实例的装饰器注册而成的agent函数，提交任务到Postgres队列
    4. 立即返回包含 task_id 的响应，客户端可用此 ID 轮询结果
    """

    # --- 1. 校验文件扩展名 ---
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="未提供文件名")
    # 通过后缀判断文件类型（简单的客户端校验，更严谨的做法是检查文件头魔数）
    if not (
        filename.endswith('.csv') or filename.endswith('.xlsx') or filename.endswith('.xls')):
        raise HTTPException(status_code=400, detail="只支持 .csv 或 .xlsx/.xls 格式的文件")


    # --- 2. 保存上传文件 ---
    # 使用 uuid 生成唯一前缀，防止文件名冲突
    safe_filename = f"{uuid.uuid4()}_{Path(filename).name}"
    file_path = UPLOAD_DIR / safe_filename
    # 写入文件：以二进制模式打开，用 shutil.copyfileobj 将上传的文件内容流式拷贝到磁盘
    # 使用 with 语句自动关闭文件句柄，保证资源正确释放
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)


    # --- 3. 生成任务到 Postgres 队列 ---
    # 生成业务 task_id
    task_id = str(uuid.uuid4())
    # 在 tasks 表插入 pending 记录
    await update_task_db(task_id=task_id, status='pending')
    # 将任务放入 Procrastinate 队列
    await run_analysis_task.defer_async(file_path=str(file_path), task_id=task_id)


    # --- 4. 立即返回 AnalysisResponse ---
    # 客户端收到此 JSON，知道任务已创建，后续用 task_id 查询进度
    return AnalysisResponse(
        task_id=task_id,
        status="pending",
        message="文件已上传，分析任务已提交",
    )


# ===========================
# 端点 2：查询任务状态 / 结果
# ===========================
@router.get("/{task_id}", response_model=AnalysisResult)
async def get_analysis_status(task_id: str):
    """
    轮询分析任务状态和结果。

    客户端可使用 POST /upload 返回的 task_id 不断调用此接口，
    直到 status 变为 "completed" 或 "failed"。

    返回值使用 AnalysisResult 模型，字段包括：
    - task_id: 任务 ID
    - status: "pending" / "running" / "completed" / "failed"
    - summary: 当任务完成时，返回分析结论文本
    - error: 当任务失败时，返回错误描述
    - result_files: 生成的结果文件列表（本例中可能包含图表文件名）
    """

    task = await get_task_from_db(task_id=task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 构造响应模型，Pydantic 会自动过滤掉多余字段
    return AnalysisResult(
        task_id=task_id,
        status=task["status"],
        summary=task.get("summary"),
        error=task.get("error"),
        # 使用 chart_available 字段生成 result_files 提示
        chart_available=task.get("chart_available", False),
    )


# ===========================
# 端点 3：下载分析图表
# ===========================
@router.get("/{task_id}/chart")
async def get_chart(task_id: str):
    """
    获取分析任务生成的可视化图表图片。

    只有当任务状态为 "completed" 且 chart_available 为 True 时，并且拿到了表中的task_id时
    才会返回图片，否则返回 404。

    返回的图片 MIME 类型为 image/png，前端可直接用 <img> 标签加载。
    """
    # 1. 查找任务
    task = await get_task_from_db(task_id=task_id)
    if task is None or task['status'] != "completed" or not task.get("chart_available"):
        raise HTTPException(status_code=404, detail="图表未生成或任务未完成")

    chart_path = task.get("chart_path")
    if not chart_path or not Path(chart_path).exists():
        raise HTTPException(status_code=404, detail="图表文件丢失")

    return FileResponse(path=chart_path, media_type="image/png", filename=f"{task_id}_chart.png")
