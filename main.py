import os
from typing_extensions import TypedDict
from langgraph.graph import StateGraph

from dotenv import load_dotenv,find_dotenv
load_dotenv(find_dotenv())

api_key = os.environ["LLM_API_KEY"]
api_base = os.environ["LLM_API_BASE"]
model_small=os.environ['LLM_BAK_MODEL']
class GraphState(TypedDict):
    flag : str
    generation : str

initial_prompt = 'hello'
def start_node(state:GraphState):
    return {"generation": initial_prompt, "flag": "start"}

def process_node(state: GraphState):
    return {"generation": state["generation"], "flag": "process"}

def end_node(state: GraphState):
    return {"generation": state["generation"], "flag": "end"}

workflow = StateGraph(GraphState)

workflow.add_node("start", start_node)  # generation solution
workflow.add_node("process", process_node)  # check code
workflow.add_node("end", end_node)  # reflect

workflow.set_entry_point("start")
workflow.add_edge("start", "process")
workflow.add_edge("process", "end")

app = workflow.compile()
final_state = app.invoke({"flag": "start", "generation": concatenated_content})
print(final_state)