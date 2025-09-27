from typing import TypedDict, Literal

from langgraph.graph import StateGraph, START, END


class PortfolioState(TypedDict):
    amount_usd: float
    total_usd: float
    target_currency: Literal["BDT", "EUR"]
    total: float


def calc_total(state: PortfolioState) -> PortfolioState:
    state['total_usd'] = state['amount_usd'] * 1.08
    return state


def convert_to_bdt(state: PortfolioState) -> PortfolioState:
    state['total'] = state['total_usd'] * 121
    return state


def convert_to_eur(state: PortfolioState) -> PortfolioState:
    state['total'] = state['total_usd'] * 0.9
    return state

def convert_to_aus(state: PortfolioState) -> PortfolioState:
    state['total'] = state['total_usd'] * 12
    return state


def choose_conversion(state: PortfolioState) -> str:
    return state["target_currency"]


builder = StateGraph(PortfolioState)

builder.add_node("calc_total_node", calc_total)
builder.add_node("convert_to_bdt_node", convert_to_bdt)
builder.add_node("convert_to_eur_node", convert_to_eur)
builder.add_node("convert_to_aus_node", convert_to_aus)

builder.add_edge(START, "calc_total_node")
builder.add_conditional_edges(
    "calc_total_node",
    choose_conversion,
    {
        "BDT": "convert_to_bdt_node",
        "EUR": "convert_to_eur_node",
        "AUS": "convert_to_aus_node",
    }
)
builder.add_edge(["convert_to_bdt_node", "convert_to_eur_node", "convert_to_aus_node"], END)

graph = builder.compile()

with open("diagram/cond_graph.mmd", "w") as f:
    f.write(graph.get_graph().draw_mermaid())

res = graph.invoke({"amount_usd": 1000, "target_currency": "BDT"})

print(res)
