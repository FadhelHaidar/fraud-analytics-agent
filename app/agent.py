from typing import Any, Dict, List, Optional
import asyncio
from langgraph.prebuilt import create_react_agent

from app.config import get_llm
from app.prompt import system_prompt


# minimal knobs without overengineering
DEFAULT_HISTORY_MAX = 20
DEFAULT_TIMEOUT_SEC = 180


def _last_assistant_text(messages: list) -> str:
    for m in reversed(messages):
        role = getattr(m, "role", None) or (m.get("role") if isinstance(m, dict) else None)
        content = getattr(m, "content", None) or (m.get("content") if isinstance(m, dict) else None)

        if role == "assistant" or m.__class__.__name__ == "AIMessage":
            if content:
                return str(content)

    # fallback if nothing matched
    if messages:
        last = messages[-1]
        return getattr(last, "content", None) or (last.get("content") if isinstance(last, dict) else "")
    return ""


async def get_response(
    query: str,
    chat_history: List[Dict[str, Any]],
    tools: List[Any],
    *,
    history_max: int = DEFAULT_HISTORY_MAX,
    timeout_sec: int = DEFAULT_TIMEOUT_SEC,
) -> str:
    
    history = chat_history[-history_max:] if chat_history else []

    user_message = {"role": "user", "content": query}
    messages = history + [user_message]

    agent = create_react_agent(
        model=get_llm(),           # your init_chat_model wrapper
        tools=tools,               # whatever tools you pass
        prompt=system_prompt,      # your system prompt
    )

    try:
        response = await asyncio.wait_for(
            agent.ainvoke({"messages": messages}),
            timeout=timeout_sec
        )
        return _last_assistant_text(response.get("messages", [])) or "..."
    except asyncio.TimeoutError:
        return "Sorry, the model took too long. Please try again."
    except Exception as e:
        # Keep it simple; log in your route/middleware if you want details.
        return f"Error: {e}"
