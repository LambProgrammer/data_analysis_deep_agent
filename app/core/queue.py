# 使用专门为 PostgreSQL 设计的任务队列库 Procrastinate，
# 自带任务状态持久化、重试、调度、锁定等企业级特性

# 创建 Procrastinate 应用实例


from procrastinate import App as ProcrastinateApp
from procrastinate import PsycopgConnector

# from procrastinate import SyncPsycopgConnector
from config import config

if config.DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL 未配置，请在 .env 中设置")


connector = PsycopgConnector(conninfo=config.DATABASE_URL)

# 只有一个 Procrastinate 实例，连接你的 PostgreSQL
app = ProcrastinateApp(connector=connector)
