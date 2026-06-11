# ==========================================
# 单元测试：config.py
# ==========================================

from config import Config


def test_get_database_url_container():
    """容器环境下，返回用服务名 postgres 的连接串"""
    config = Config(ENVIRONMENT="container")
    url = config.get_database_url()
    assert url == "postgresql://postgres:postgres@postgres:5432/analysis"


def test_get_database_url_development_with_env():
    """开发环境下，优先使用 DATABASE_URL 环境变量"""
    config = Config(
        ENVIRONMENT="development",
        DATABASE_URL="postgresql://dev_user:dev_pass@dev_host:5432/dev_db",
    )
    url = config.get_database_url()
    assert url == "postgresql://dev_user:dev_pass@dev_host:5432/dev_db"


def test_get_database_url_development_fallback():
    """开发环境下，如果没有设置 DATABASE_URL，返回 localhost 默认值"""
    config = Config(ENVIRONMENT="development", DATABASE_URL=None)
    url = config.get_database_url()
    assert url == "postgresql://postgres:postgres@localhost:5432/analysis"
