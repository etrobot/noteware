import os

from llama_index.core.agent import ReActAgent
from llama_index.core.llms import ChatMessage
from llama_index.core.tools import BaseTool, FunctionTool
from llama_index.llms.openai_like import OpenAILike

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

def multiply(a: int, b: int) -> int:
    """Multiply two integers and returns the result integer"""
    return a * b
multiply_tool = FunctionTool.from_defaults(fn=multiply)

def add(a: int, b: int) -> int:
    """Add two integers and returns the result integer"""
    return a + b
add_tool = FunctionTool.from_defaults(fn=add)

api_key = os.environ["LLM_API_KEY"]
api_base = os.environ["LLM_API_BASE"]
model_small=os.environ['LLM_BAK_MODEL']

llm = OpenAILike(is_chat_model=True, model="THUDM/glm-4-9b-chat", api_base=api_base, api_key=api_key)

agent = ReActAgent.from_tools([multiply_tool, add_tool], llm=llm, verbose=True)

response = agent.chat("What is 20+(2*4)? Calculate step by step ")