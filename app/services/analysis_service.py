import uuid
from pathlib import Path

from app.core.dependencies import task_sandbox_agent
from app.core.queue import app as procrastinate_app
from app.utils.db import update_task_db

# 图表保存的固定位置（必须在 ./data/ 下）
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


@procrastinate_app.task(name="run_analysis")
async def run_analysis_task(file_path: str, task_id: str):
    """
    由 Procrastinate Worker 调用的任务函数。
    成功时返回结果字典，失败时自动记录异常。
    """

    # 校验 file_path 在允许的目录内
    uploads_dir = DATA_DIR / "uploads"
    resolved_path = Path(file_path).resolve()
    if not str(resolved_path).startswith(str(uploads_dir.resolve())):
        raise ValueError(f"非法的文件路径: {file_path}")

    # 更新状态为 running
    await update_task_db(task_id=task_id, status='running')

    try:
        async with task_sandbox_agent() as (sandbox, agent):
            # ========== 上传文件到沙箱 ==========
            remote_filename = f"/data/{task_id}_{Path(file_path).name}"
            await sandbox.filesystem.copy_from_local.aio(file_path, remote_filename)

            # 最新的优化后指令
            input_message = {
                "role": "user",
                "content": (
                    f"分析文件 {remote_filename}，完成探索性数据分析并给出至少3个关键发现。\n"
                    "如果是 Excel 文件，用 pandas.read_excel() 读取。\n\n"

                    "## 核心规则（覆盖默认行为，必须严格遵守）\n"
                    "1. **直接分析，禁止提前读文件**：用 pandas 直接读取文件，绝对不要先用 read_file 查看内容。\n"
                    "2. **所有操作合并为一次执行**：将数据读取、分析计算、图表绘制、报告写入全部写在一个 python -c 命令中，一次性执行完毕。\n"
                    "3. **结束后直接总结，禁止验证**：代码执行成功后立刻输出最终总结，绝对不要使用 ls、read_file 等命令检查文件。\n\n"

                    "## 问题解决策略（避免陷入死循环）\n"
                    "- 如果第一次执行代码后出现错误，不要尝试小修小补（如修改单个变量、调整参数）。\n"
                    "- 你应该**根据错误信息，重新设计一段全新的完整代码**，确保逻辑清晰、一步到位，然后立即执行。\n"
                    "- 如果连续两次执行都失败，**立刻停止执行代码**，用中文总结当前已发现的问题和已完成的分析，不要继续尝试。\n\n"

                    "## 输出要求\n"
                    f"- 图表保存为 {task_id}_chart.png，dpi=150，所有文字使用英文。\n"
                    f"- 分析报告保存为 {task_id}_analysis.txt，使用中文撰写。\n\n"

                    "## 路径约定\n"
                    "工作目录为 /data，保存文件时直接写文件名，不加路径前缀。\n\n"

                    "## 环境\n"
                    "python3、pandas、matplotlib、openpyxl 已预装，直接 import 使用。"
                )
            }


            # ========== 带有步数限制和兜底总结的 Agent 执行 ==========
            messages = [input_message]
            thread_id = str(uuid.uuid4())

            config = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 10  # 足够完成 2 次 execute 的安全限制
            }

            try:
                result = await agent.ainvoke(
                    {"messages": messages},                             # type: ignore
                    config=config                                       # type: ignore
                )
                messages = result["messages"]
            except Exception as e:
                # 如果是因为递归限制触发的错误，注入强制总结消息再试一次
                if "Recursion limit" in str(e) or "GRAPH_RECURSION_LIMIT" in str(e):
                    stop_message = {
                        "role": "user",
                        "content": (
                            "已达到最大执行步数。请立刻停止编写和运行代码。"
                            "根据当前已有的分析结果，用中文输出最终总结，内容应包括："
                            "1) 已发现的数据关键发现（至少3条，如果数据不足就基于已运行的部分说明）"
                            "2) 已生成的文件列表（图表、报告等）"
                            "3) 如果图表或报告未成功生成，请说明原因"
                        )
                    }
                    messages.append(stop_message)
                    # 再次调用，这次设更小的 recursion_limit 确保快速结束
                    try:
                        result = await agent.ainvoke(
                            {"messages": messages},                             # type: ignore
                            config={
                                "configurable": {"thread_id": thread_id},
                                "recursion_limit": 4
                            }
                        )
                        messages = result["messages"]
                    except Exception:
                        # 如果还是失败，就用最后一次的消息内容作为总结
                        pass
                else:
                    raise  # 其他异常直接抛给外层处理

            # 无论正常结束还是兜底，最后一条消息即为最终回答
            final_answer = messages[-1].content                                 # type: ignore

            # --- 下载产物到本地 ---
            local_chart = DATA_DIR / f"{task_id}_chart.png"
            local_report = DATA_DIR / f"{task_id}_analysis.txt"
            chart_available = False

            # 图表下载
            chart_remote = f"/data/{task_id}_chart.png"
            try:
                await sandbox.filesystem.copy_to_local.aio(chart_remote, str(local_chart))
                chart_available = True
            except Exception as e:
                final_answer += f"\n\n（注意：图表下载失败 ({type(e).__name__}: {e})）"

            # 报告下载
            report_remote = f"/data/{task_id}_analysis.txt"
            try:
                await sandbox.filesystem.copy_to_local.aio(report_remote, str(local_report))
            except Exception as e:
                final_answer += f"\n\n（注意：报告下载失败 ({type(e).__name__}: {e})）"

            # 更新数据库 tasks 表
            await update_task_db(
                task_id=task_id,
                status='completed',
                summary=final_answer,
                chart_path=str(local_chart) if chart_available else None,
                chart_available=chart_available,
            )

    except Exception as e:
        await update_task_db(task_id=task_id, status='failed', error=str(e))
        raise
