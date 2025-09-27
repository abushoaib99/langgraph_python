from typing import Annotated

from decouple import config
from typing_extensions import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

GEMINI_API_KEY = config("GEMINI_API_KEY")

memory = MemorySaver()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0
)

class State(TypedDict):
    messages: Annotated[list, add_messages]

def chatbot(state: State) -> State:
    return {"messages": [llm.invoke(state["messages"])]}

builder = StateGraph(State)
builder.add_node("chatbot_node", chatbot)

builder.add_edge(START, "chatbot_node")
builder.add_edge("chatbot_node", END)

graph = builder.compile(checkpointer=memory)

with open("diagram/memory.mmd", "w") as f:
    f.write(graph.get_graph().draw_mermaid())

config = {'configurable': {'thread_id': '1'}}

while True:
    in_message = input("You: ")
    if in_message.lower() in {"quit","exit"}:
        break

    state: State = {
        "messages": [{"role": "user", "content": in_message}]
    }

    state = graph.invoke(input=state, config=config)
    print("Bot:", state["messages"][-1].content, '\n\n')
