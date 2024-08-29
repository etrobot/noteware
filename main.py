import os
import re
import requests
from typing_extensions import TypedDict
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv,find_dotenv
load_dotenv(find_dotenv())

api_key = os.environ["LLM_API_KEY"]
api_base = os.environ["LLM_API_BASE"]
model_small=os.environ['LLM_BAK_MODEL']
class GraphState(TypedDict):
    flag : str
    generation : str


def llmSummarize(text: str) -> str:
    llm = ChatOpenAI(model=model_small, api_key=api_key, base_url=api_base)
    content = text+'\n summarize and output keypoints with index.'
    result = llm.invoke(content).content
    return result

def start_node(state:GraphState):
    image_extensions = r'\.(jpg|jpeg|png|gif|bmp|svg|webp)$'
    if re.search(image_extensions, state["generation"], re.IGNORECASE):
        raise ValueError("Not a valid link")
    content = requests.get('https://r.jina.ai/'+state["generation"], headers={'User-Agent': 'Mozilla/5.0'}).text
    return {"generation": content, "flag": "start"}

def process_node(state: GraphState):
    result = llmSummarize(state["generation"])
    return {"generation": result, "flag": "process"}

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
user_input = input("URL: ")
final_state = app.invoke({"flag": "start", "generation": user_input})
print(final_state)