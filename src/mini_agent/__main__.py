import sys
from mini_agent.agent import agent_loop

if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    # messages 列表跨轮复用：agent_loop 以副作用方式向其追加
    # assistant / tool 消息，调用方无需手动 append assistant 回复。
    # 详见 agent.agent_loop 的 docstring 契约。
    messages = [{"role": "system", "content": "你是一个助手，通过调用工具完成任务。"}]

    # 命令行首条任务（可选）：与交互循环走同一套路径，
    # 保证 argv 分支后 messages 状态完整，后续追问上下文不丢。
    if len(sys.argv) > 1:
        messages.append({"role": "user", "content": sys.argv[1]})
        reply = agent_loop(messages)
        print(reply)

    while True:
        try:
            user_input = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input or user_input.lower() in ("exit", "quit"):
            break
        messages.append({"role": "user", "content": user_input})
        reply = agent_loop(messages)
        print(reply)
