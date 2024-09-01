import os
import traceback
import re
import logging
from colorlog import ColoredFormatter
from notion import NotionMarkdownManager
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

def setup_logger():
    formatter = ColoredFormatter(
        "%(log_color)s%(levelname)s:%(message)s",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )

    logger = logging.getLogger('example')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    return logger

def read_and_execute_app():
    logger = setup_logger()

    try:
        manager = NotionMarkdownManager(os.getenv("NOTION_TOKEN"), os.getenv("NOTION_DB_ID"))
        template_articles = manager.list_template_articles()
        selected_article_id = manager.display_article_menu(template_articles)
        logger.info(selected_article_id)
        if selected_article_id:
            notion_content = manager.get_article_content(selected_article_id)
        logger.info(notion_content)
        with open('app_template.py', 'r') as master_file:
            app_content = master_file.read()

        llm = ChatOpenAI(model=os.getenv("MODEL"), api_key=os.getenv("LLM_KEY"), base_url=os.getenv("LLM_BASE"))
        new_app = llm.invoke(f'<app_template>{app_content}</app_template>\n <Instruction>{notion_content}</Instruction> follow the template to convert the workflow into a langgraph app, replace user input with mission as initial parameter. Only output the final python code').content
        logger.info(new_app)
    except Exception as e:
        logger.error(f"Error reading app_template.py: {e}")
        return

    try:
        namespace = {}
        match = re.search(r'```python\s*\n\s*(.*?)\s*\n\s*```', new_app, re.DOTALL)
        python_code = match.group(1)
        logger.info(python_code)
        exec(python_code, namespace)
    except Exception as e:
        logger.error("Error executing app_template.py content:")
        traceback.print_exc()

if __name__ == "__main__":
    read_and_execute_app()