import operator
from typing import TypedDict, Annotated, Any, List, Dict
from langchain_core.messages import AnyMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, END
from src.utils import get_llm
from src.prompt import system_prompt

DEFAULT_HISTORY_MAX = 20
DEFAULT_TIMEOUT_SEC = 180

class AgentState(TypedDict):
    messages: Annotated[List[AnyMessage], operator.add]
    chunks: Annotated[List[Dict[str, Any]], operator.add]
    sql:     Annotated[List[str], operator.add]

class Agent:
    def __init__(self, model, tools, system_prompt=""):
        self.system_prompt = system_prompt
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_llm)
        graph.add_node("action", self.take_action)
        graph.add_conditional_edges("llm", self.exists_action, {True: "action", False: END})
        graph.add_edge("action", "llm")
        graph.set_entry_point("llm")
        self.graph = graph.compile()

        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)

    def exists_action(self, state: AgentState):
        result = state["messages"][-1]
        return len(result.tool_calls) > 0

    def call_llm(self, state: AgentState):
        messages = state["messages"]
        if self.system_prompt:
            messages = [SystemMessage(content=self.system_prompt)] + messages
        message = self.model.invoke(messages)
        return {"messages": [message]}

    def take_action(self, state: AgentState):
        tool_calls = state["messages"][-1].tool_calls
        results = []
        new_chunks, new_sql = [], []

        for t in tool_calls:
            if t["name"] not in self.tools:
                result = {"answer": "bad tool name, retry", "chunks": [], "sql": None}
            else:
                result = self.tools[t["name"]].invoke(t["args"])

            # collect extras
            if result.get("chunks"):
                new_chunks.extend(result["chunks"])
            if result.get("sql"):
                new_sql.append(result["sql"])

            results.append(
                ToolMessage(
                    tool_call_id=t["id"],
                    name=t["name"],
                    content=result.get("answer", "")
                )
            )

        return {
            "messages": results,
            "chunks": new_chunks,
            "sql": new_sql,
        }


def get_response(
        query: str, 
        chat_history: List[Dict[str, Any]], 
        tools: List[Any], *, 
        history_max: int = DEFAULT_HISTORY_MAX, 
    ) -> dict[str, Any]:
    
    if not query.strip():
        return {"messages": [], "chunks": [], "sql": []}
    
    if chat_history and len(chat_history) > history_max:
        history = chat_history[-history_max:]
    else:
        history = chat_history or []

    messages = history + [{"role": "user", "content": query}]
    agent = Agent(model=get_llm(), tools=tools, system_prompt=system_prompt)
    result = agent.graph.invoke({"messages": messages})
    
    return {
        "response": result.get("messages", [])[-1].content if result.get("messages") else "",
        "chunks": result.get("chunks", []),
        "sql": result.get("sql", []),
    }