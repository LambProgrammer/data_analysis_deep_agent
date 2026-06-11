from langchain_deepseek import ChatDeepSeek
from pydantic import SecretStr

from config import config

_llm_deepseek = None

def get_deepseek_llm():
    """惰性初始化 DeepSeek LLM 实例，避免缺 Key 时启动崩溃"""
    global _llm_deepseek
    if _llm_deepseek is None:
        api_key = config.DEEPSEEK_API_KEY
        if api_key is None:
            raise ValueError("DEEPSEEK_API_KEY 未在 .env 中设置")
        _llm_deepseek = ChatDeepSeek(
            model=config.DEEPSEEK_CHAT,
            api_key=SecretStr(api_key)
        )
    return _llm_deepseek



# print(llm_hunyuan.invoke("你好。").content)
