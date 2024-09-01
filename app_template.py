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

    def extract_and_replace_links(self,text:str)->dict:
        url_pattern = r'(https?://[^\s]+|www\.[^\s]+)'
        links = re.findall(url_pattern, text)
        for i, link in enumerate(links):
            text = text.replace(link, f'[link{i + 1}]')
        return {'links': links, 'text': text}
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
    mission: str
    next : str
    generation : str

def run(user_input:str,tools:tools) -> str:
    def entry_node(state: GraphState):
        etracted = tools.extract_and_replace_links(state["mission"])
        if len(etracted['links']) > 0:
            generation = tools.linkReader(etracted['links'][0])
        else:
            search_result = tools.serp(etracted['links'][0])
            generation = '\n'.join([x['body'] for x in search_result])
        return {"generation": generation, "next": "process", "mission": etracted['text']}

    def process_node(state: GraphState):
        result = tools.summarize(state["generation"])
        return {"generation": result, "next": "think", "mission": state["mission"]}

    def think_node(state: GraphState):
        # this node is a conditional node that will return different states
        think_result = tools.llm.invoke('data:' + state["generation"] + 'mission:' + state[
            "mission"] + "\nThink: if the data can fit the mission, output 'yes', otherwise make new keyworks output begin with 'Should search with:'.").content
        if 'Should search with:' not in think_result:
            return {"generation": state["generation"], "next": END, "mission": state["mission"]}
        else:
            return {"generation": think_result.split('Should search with:')[1], "next": "entry",
                    "mission": state["mission"]}

    def conditional_edge(state: GraphState):
        return state['next']

    workflow = StateGraph(GraphState)

    workflow.add_node("entry", entry_node)
    workflow.add_node("process", process_node)
    workflow.add_node("think", think_node)

    workflow.set_entry_point("entry")
    workflow.add_edge("entry", "process")
    workflow.add_edge("process", "think")
    workflow.add_conditional_edges("think", conditional_edge)  #only conditional node requires adding conditional edge

    app = workflow.compile()
    final_state = app.invoke({"next": "entry", "mission": user_input},{"recursion_limit": 10}, debug=True)
    NotionMarkdownManager(os.getenv("NOTION_TOKEN"), os.getenv("NOTION_DB_ID")).insert_markdown_to_notion(
        final_state["generation"], user_input)

run(input("misson: "),tools())# change input to directly pass a mission