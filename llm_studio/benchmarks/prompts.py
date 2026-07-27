"""Built-in benchmark prompts."""

PROMPT_SETS: dict[str, list[str]] = {
    "default": [
        "用三句话解释 Windows 上本地大模型推理的基本流程。",
        "总结下面这段话的要点：低显存设备需要控制上下文长度、量化方式和并发请求。",
        "解释这段 Python 代码的作用：def add(a, b): return a + b",
        "第一轮我说苹果，第二轮我说香蕉。请回答第一轮我说了什么。",
        "请按 RAG 回答格式输出：结论、依据、限制。",
    ]
}


def get_prompt_set(name: str) -> list[str]:
    return PROMPT_SETS.get(name, PROMPT_SETS["default"])
