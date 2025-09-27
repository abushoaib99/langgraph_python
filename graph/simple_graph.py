from typing import TypedDict

from langgraph.graph import StateGraph, START, END


class PortfolioState(TypedDict):
    amount_usd: float
    total_usd: float
    total_bdt: float


def calc_total(state: PortfolioState) -> PortfolioState:
    state["total_usd"] = state["amount_usd"] * 1.08
    return state


def convert_to_bdt(state: PortfolioState) -> PortfolioState:
    state["total_bdt"] = state["total_usd"] * 121
    return state


builder = StateGraph(PortfolioState)

builder.add_node("calc_total_node", calc_total)
builder.add_node("convert_to_bdt_node", convert_to_bdt)

builder.add_edge(start_key=START, end_key="calc_total_node")
builder.add_edge(start_key="calc_total_node", end_key="convert_to_bdt_node")
builder.add_edge(start_key="convert_to_bdt_node", end_key=END)

graph = builder.compile()

with open("diagram/simple_graph.mmd", "w") as f:
    f.write(graph.get_graph().draw_mermaid())



res = graph.invoke({"amount_usd": 1000, "total_bdt": 3000})

print(res)



