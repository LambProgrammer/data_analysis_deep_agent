# ==========================================
# 本文件用于测试，确认能够连接到Modal刚部署的 App 并创建一个沙箱
# 测试时终端运行：python test_modal_sandbox.py
# ==========================================


# test_modal_sandbox.py
import modal
from langchain_modal import ModalSandbox

def main():
    # 1. 创建一个预装好依赖的镜像
    image = (
        modal.Image.debian_slim()
        .pip_install("pandas", "matplotlib", "openpyxl")
    )

    # 2. 查找已部署的 App (确保你已经执行过 modal deploy app/core/modal_app.py)
    app = modal.App.lookup("data-analysis-agent")

    # 3. 创建一个 Sandbox (同步方式)
    sandbox = modal.Sandbox.create(
        app=app,
        image=image,
        timeout=120,
        workdir="/data",
    )
    print("Sandbox created:", sandbox)

    # 4. 用 ModalSandbox 适配器包装 (后续给 Agent 使用)
    backend = ModalSandbox(sandbox=sandbox)

    # 5. 测试执行命令
    # 使用 sandbox.exec() 来在沙箱中运行命令
    process = sandbox.exec("python", "-c", "import pandas; print('pandas version:', pandas.__version__)")
    print(process.stdout.read())
    process = sandbox.exec("python", "-c", "import matplotlib; print('matplotlib version:', matplotlib.__version__)")
    print(process.stdout.read())
    process = sandbox.exec("python", "-c", "import openpyxl; print('openpyxl version:', openpyxl.__version__)")
    print(process.stdout.read())

    print("\nAll dependencies verified!")

    # 6. (重要!) 测试完成后，务必终止沙箱以释放资源
    sandbox.terminate()
    print("Sandbox terminated.")

if __name__ == "__main__":
    main()