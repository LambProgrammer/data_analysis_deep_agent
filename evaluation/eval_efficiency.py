"""
数据分析 Agent 效率评估脚本 (终极版)
1. 运行评估实验
2. 自动定位最新实验，汇总真实的 Token 和延迟
3. 将评分直接写回 LangSmith
全程无需手动干预，一次运行到位。
"""

# ==============================
# 1. 环境与依赖
# ==============================
from dotenv import load_dotenv
load_dotenv()

import sys, os, asyncio, uuid
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langsmith import Client, evaluate, traceable
from app.core.dependencies import task_sandbox_agent

# ==============================
# 2. 评估阈值
# ==============================
MAX_LATENCY_SECONDS = 60
MAX_TOTAL_TOKENS = 120_000

# ==============================
# 3. 目标函数 (运行你的 Agent)
# ==============================
@traceable
async def run_agent_async(inputs: dict) -> dict:
    instruction = inputs["instruction"]
    file_path = inputs["file_path"]
    task_id = f"eval_{Path(file_path).stem}"

    async with task_sandbox_agent() as (sandbox, agent):
        remote_filename = f"/data/{task_id}_{Path(file_path).name}"
        await sandbox.filesystem.copy_from_local.aio(file_path, remote_filename)

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
            "recursion_limit": 10
        }

        try:
            result = await agent.ainvoke(
                {"messages": messages},                         # type: ignore
                config=config                                   # type: ignore
            )
            messages = result["messages"]
        except Exception as e:
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
                try:
                    result = await agent.ainvoke(
                        {"messages": messages},                 # type: ignore
                        config={
                            "configurable": {"thread_id": thread_id},
                            "recursion_limit": 4
                        }
                    )
                    messages = result["messages"]
                except Exception:
                    pass
            else:
                raise

        final_answer = messages[-1].content                     # type: ignore

        # 下载图表（评估用）
        chart_path = None
        try:
            temp_dir = Path("evaluation/temp")
            temp_dir.mkdir(parents=True, exist_ok=True)
            local_chart = str(temp_dir / f"{task_id}_chart.png")
            await sandbox.filesystem.copy_to_local.aio(f"/data/{task_id}_chart.png", local_chart)
            chart_path = local_chart
        except Exception:
            pass

    return {"output": final_answer, "chart_path": chart_path}


def run_agent_sync(inputs: dict) -> dict:
    return asyncio.run(run_agent_async(inputs))


# ==============================
# 4. 评分逻辑（自动定位实验，汇总数据）
# ==============================
def score_experiment(client, experiment_name):
    print(f"\n正在为实验 '{experiment_name}' 自动评分...")

    all_runs = list(client.list_runs(project_name=experiment_name))

    root_run = None
    for run in all_runs:
        if run.parent_run_id is None:
            root_run = run
            break

    if not root_run:
        print("❌ 未找到根 Run，评分失败")
        return

    total_tokens = root_run.total_tokens or 0

    start_times = [run.start_time for run in all_runs if run.start_time]
    end_times = [run.end_time for run in all_runs if run.end_time]
    if start_times and end_times:
        total_latency = (max(end_times) - min(start_times)).total_seconds()
    else:
        total_latency = 0.0

    token_score = 1.0 if total_tokens <= MAX_TOTAL_TOKENS else 0.0
    latency_score = 1.0 if total_latency <= MAX_LATENCY_SECONDS else 0.0

    client.create_feedback(
        run_id=root_run.id,
        key="token_usage",
        score=token_score,
        comment=f"总 Token: {total_tokens} (阈值 {MAX_TOTAL_TOKENS})"
    )
    client.create_feedback(
        run_id=root_run.id,
        key="latency",
        score=latency_score,
        comment=f"总延迟 {total_latency:.1f}s (阈值 {MAX_LATENCY_SECONDS}s)"
    )
    print(f"✅ 评分完成！Token: {token_score} ({total_tokens}), 延迟: {latency_score} ({total_latency:.1f}s)")


# ==============================
# 5. 主流程
# ==============================
def main():
    client = Client()
    dataset_name = "efficiency-baseline"

    print(f"正在基于数据集 '{dataset_name}' 运行 Agent 评估...")
    print("⚠️  这将真实调用 DeepSeek API 和 Modal 沙箱，请耐心等待。")

    experiment = evaluate(
        run_agent_sync,
        data=dataset_name,
        experiment_prefix="efficiency-live",
        client=client,
    )

    print(f"实验运行完成: {experiment.experiment_name}")

    score_experiment(client, experiment.experiment_name)

    print(f"\n在线查看完整结果: {experiment.url}")


if __name__ == "__main__":
    main()