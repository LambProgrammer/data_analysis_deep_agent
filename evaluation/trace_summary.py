"""
LangSmith仪表盘Trace内容提取
运行评估实验，获取Run ID，再运行本文件，得到本次Agent运行时所有步骤、节点的内容、耗时、Token消耗
"""


from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

client = Client()

# 从你分享的链接中取到的根 Run ID
ROOT_RUN_ID = "019e730f-3cdb-71c1-b8d9-5a1cdc248117"
# 从上一轮 JSON 里确认的 tracing project 名称
PROJECT_NAME = "efficiency-live-11452a09"

# 1. 获取根 Run（只需要基本信息）
root_runs = list(client.list_runs(run_ids=[ROOT_RUN_ID]))
if not root_runs:
    print("❌ 根 Run 未找到，请检查 ROOT_RUN_ID")
    exit(1)
root = root_runs[0]

print("正在拉取该 Trace 下的所有节点...")

# 2. 用 trace_id 一次性获取同一个 Trace 下的所有 Run
#    如果 SDK 不支持 trace_id 参数，备选方案见文末
try:
    all_runs = list(client.list_runs(project_name=PROJECT_NAME, trace_id=root.id))
except TypeError:
    # 备选：拉取项目全部 Run 然后手动过滤
    all_runs = [
        r for r in client.list_runs(project_name=PROJECT_NAME)
        if r.trace_id == root.id
    ]

# 3. 按开始时间排序
all_runs.sort(key=lambda r: r.start_time or "")

print("=" * 80)
print(f"Trace 总览: {root.name}")
print(f"根 Run ID: {root.id}")
print(f"总 Token: {root.total_tokens or 0}")
if root.start_time and root.end_time:
    print(f"总耗时: {(root.end_time - root.start_time).total_seconds():.1f}s")
print(f"节点总数: {len(all_runs)}")
print("=" * 80)

# 4. 逐个输出关键信息
for i, run in enumerate(all_runs):
    name = run.name or "unnamed"
    run_type = run.run_type or "unknown"
    latency = ""
    if run.start_time and run.end_time:
        latency = f"{(run.end_time - run.start_time).total_seconds():.2f}s"
    tokens = run.total_tokens or 0
    prompt_tokens = run.prompt_tokens or 0
    completion_tokens = run.completion_tokens or 0
    print(f"{i+1}. [{run_type}] {name}")
    print(f"   耗时: {latency}, Token: {tokens} "
          f"(prompt: {prompt_tokens}, completion: {completion_tokens})")

print("=" * 80)
