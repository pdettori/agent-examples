from langgraph.graph import StateGraph, MessagesState, START
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_ollama import ChatOllama
import os

def get_mcpclient():
    return MultiServerMCPClient({
        "math": {
            "url": os.getenv("MCP_URL", "http://localhost:8000/sse"),
            "transport": "sse",
        }
    }
    )

async def get_graph(client) -> StateGraph:

    llm = ChatOllama(
        model="llama3.1",
        openai_api_key="http://localhost:11434/v1",
        openai_api_base="dummy",
        temperature=0,
    )
    llm_with_tools = llm.bind_tools(client.get_tools())

    # System message
    sys_msg = SystemMessage(content="You are a helpful assistant tasked with providing weather information. You must use the provided tools to complete your task.")

    # Node
    def assistant(state: MessagesState):
        return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

    # Build graph
    builder = StateGraph(MessagesState)
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(client.get_tools()))
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges(
        "assistant",
        tools_condition,
    )
    builder.add_edge("tools", "assistant")

    # Compile graph
    graph = builder.compile()
    return graph

