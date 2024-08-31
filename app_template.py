import os,re,requests
from typing_extensions import TypedDict
from langgraph.graph import StateGraph,END
from langchain_openai import ChatOpenAI
from duckduckgo_search import DDGS
from notion import NotionMarkdownManager
from dotenv import load_dotenv,find_dotenv
load_dotenv(find_dotenv())

class tools():
    def __init__(self):
        self.llm = ChatOpenAI(model=os.getenv("MODEL"), api_key=os.getenv("LLM_KEY"), base_url=os.getenv("LLM_BASE"))

    def linkReader(self, url:str) -> str:
        image_extensions = r'\.(jpg|jpeg|png|gif|bmp|svg|webp)$'
        if re.search(image_extensions, url, re.IGNORECASE):
            raise ValueError("Not a valid link")
        content = requests.get('https://r.jina.ai/' + url, headers={'User-Agent': 'Mozilla/5.0'}).text
        return content

    def serp(self,text:str) -> list:
        with DDGS(proxy="socks5://127.0.0.1:7890") as ddgs:
            return ddgs.text(text, max_results=5)

    def summarize(self,text: str,prompt='summarize and output keypoints with index.') -> str:
        content = text + '\n'+ prompt
        result = self.llm.invoke(content).content
        return result
class GraphState(TypedDict):
    target: str
    next : str
    generation : str

def run(user_input:str,tools:tools) -> str:
    def entry_node(state: GraphState):
        search_result = tools.serp(state["target"])
        result_text = '\n'.join([x['body'] for x in search_result])
        return {"generation": result_text, "next": "process", "target": state["target"]}

    def process_node(state: GraphState):
        result = tools.summarize(state["generation"])
        return {"generation": result, "next": "think", "target": state["target"]}

    def think_node(state: GraphState):
        think_result = tools.llm.invoke('data:' + state["generation"] + 'Target:' + state[
            "target"] + "\nThink: if the data can fit the target, output 'yes', otherwise make new keyworks output begin with 'Should search with:'.").content
        if 'Should search with:' not in think_result:
            return {"generation": state["generation"], "next": END, "target": state["target"]}
        else:
            return {"generation": think_result.split('Should search with:')[1], "next": "entry",
                    "target": state["target"]}

    def conditional_edge(state: GraphState):
        return state['next']

    workflow = StateGraph(GraphState)

    workflow.add_node("entry", entry_node)
    workflow.add_node("process", process_node)
    workflow.add_node("think", think_node)  # think is a conditional node

    workflow.set_entry_point("entry")
    workflow.add_edge("entry", "process")
    workflow.add_edge("process", "think")
    workflow.add_conditional_edges("think", conditional_edge)  # conditional node must add conditional edge

    app = workflow.compile()
    final_state = app.invoke({"next": "entry", "target": user_input},{"recursion_limit": 10}, debug=True)
    NotionMarkdownManager(os.environ["NOTION_TOKEN"], os.environ["NOTION_DB_ID"]).insert_markdown_to_notion(
        final_state["generation"], user_input)

run(input("Enter question: "),tools())