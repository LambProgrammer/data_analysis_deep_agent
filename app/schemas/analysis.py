"""
Pydantic 模型（Schemas）定义模块。

这些模型用于定义 API 的请求和响应数据格式。
FastAPI 会使用这些模型自动进行数据校验、转换和文档生成。

本模块实现了“异步任务 + 轮询结果”的设计模式：
1. 客户端提交 Request → 服务端立即返回 AnalysisResponse（包含 task_id）
2. 客户端使用 task_id 轮询 → 服务端返回 AnalysisResult（包含状态和最终结果）
"""

from typing import Literal

from pydantic import BaseModel


class AnalysisResponse(BaseModel):
    """
    任务创建成功后立即返回的响应模型。

    客户端收到此响应后，应该使用 task_id 进行后续轮询，
    以获取分析任务的最终结果。
    """
    task_id: str
    status: str
    message: str



class AnalysisResult(BaseModel):
    """
    查询任务状态 / 结果时的响应模型。

    用于轮询接口（如 GET /analysis/result/{task_id}）的返回。
    字段解释：
    - task_id: 任务的唯一标识
    - status: 当前任务状态，可能的值包括：
        "pending"    - 任务已创建，等待执行
        "running"    - 任务正在执行中
        "completed"  - 任务成功完成
        "failed"     - 任务执行失败
    - summary: 当 status 为 "completed" 时，包含分析结论的字符串；其他状态可能为 None
    - error: 当 status 为 "failed" 时，包含错误描述的字符串；其他状态可能为 None
    - result_files: 生成的结果文件列表（例如图片、CSV 的文件名或下载链接）
    """
    task_id: str
    status: Literal["pending", "running", "completed", "failed"]
    summary: str | None = None           # 分析结论（任务完成时才有值）
    error: str | None = None             # 错误信息（任务失败时才有值）
    chart_available: bool = False           # 图表是否已生成
