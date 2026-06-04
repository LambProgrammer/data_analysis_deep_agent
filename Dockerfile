# ==========================================
# 基础镜像：用于 Web 和 Worker 服务
# 定义项目运行所需要的完整环境（操作系统、Python、依赖包、代码等）
# 使用方式：通过 docker compose build 命令，将项目制作成一个镜像
# 若代码后续有修改，则重新运行docker compose build，调用本文件重新构建镜像
# ==========================================

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（matplotlib 需要 libfreetype，psycopg2 需要 libpq）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfreetype6-dev \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装 Python 包
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制整个项目代码
COPY . .

# 创建运行时需要的目录
RUN mkdir -p data/uploads

# 暴露 FastAPI 默认端口
EXPOSE 8000

# 不指定 CMD，由 docker-compose 根据服务覆盖