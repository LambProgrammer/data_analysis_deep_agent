使用cloudflare内网穿透，使用任意外网设备访问：
终端执行：cloudflared tunnel --url http://localhost:8000
获取随即网址访问



开发测试时：
因代码随时修改，暂不容器化。
要使用worker+数据库+项目FastAPI的uvicorn进行测试

1、确保Docker里的数据库容器运行
2、启动Worker：python run_worker.py（不要关闭此终端）
3、新建一个终端：uvicorn app.main:app --host 0.0.0.0 --port 8000（也不要关）
    或者执行：python start_server.py   使用启动脚本运行uvicorn（开发异步项目时更常用，兼容性更好）



容器化部分：
因为 Docker 构建需要明确的依赖列表，请在项目根目录运行：uv pip freeze > requirements.txt
这会将当前虚拟环境中的所有包（包括 DeepAgents、Modal 等）导出到 requirements.txt。以后依赖变更时重新运行即可。

初始构建与启动（或代码修改后）：

    在项目根目录打开终端，执行：
    bash

    docker compose build   # 根据 Dockerfile 构建镜像
    docker compose up -d   # 根据 docker-compose.yml 创建并启动容器

    或者合并为：docker compose up -d --build

日常使用（代码未修改）：

    打开 Docker Desktop。

    在 Containers 页面，找到名为 data_analysis_deep_agent 的 Compose 项目（三个容器组成）。

    点击项目旁边的 “启动” 按钮（▶️），三个容器就会运行起来。

    访问 http://localhost:8000 测试。

    无需使用任何 CLI 命令。

代码修改后更新：

    回到项目根目录，再次执行 docker compose up -d --build（或 build + up -d）。

    之后又可以继续用 Docker Desktop 启动。