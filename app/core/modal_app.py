# ==========================================
# 这个 App 是沙箱的“大本营”，我们后续会通过 ModalSandbox 在它上面动态创建沙箱实例。
# 注意：App 名称 "data-analysis-agent" 要全局唯一（仅限你自己的账号内），如果冲突可以改名，
# 但后续代码中 modal.App.lookup() 的参数也需要同步修改。
# ==========================================


import modal

APP_NAME = "data-analysis-agent"
app = modal.App(APP_NAME)