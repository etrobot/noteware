import requests,logging,json,os,time as t
from notion import NotionMarkdownManager
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s')

class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[94m',  # blue
        'INFO': '\033[92m',   # green
        'WARNING': '\033[93m', # yellow
        'ERROR': '\033[91m',   # red
        'CRITICAL': '\033[95m' # pink
    }
    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, '')
        message = super().format(record)
        return f"{color}{message}{self.RESET}"

handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter())
logging.getLogger().addHandler(handler)

url = os.getenv("MINDSEARCH")

manager = NotionMarkdownManager(os.getenv("NOTION_TOKEN"), os.getenv("NOTION_DB_ID_SW"))

while True:
    try:
        mission_articles = manager.list_mission_articles()
        if len(mission_articles) == 0:
            logging.info("No mission articles found")
            t.sleep(60)
            continue
        for article in mission_articles:
            mission =  {"name": article["properties"]["Name"]["title"][0]["text"]["content"], "value": article["id"]}
            query = mission["name"]+'\n'+mission["value"].replace(mission["name"],'')
            message = [dict(role='user', content=query)]
            data = {'inputs': message}
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, headers=headers, data=json.dumps(data), stream=True)
            nodes = {}
            adjacency_list = {}
            answer = ""
            current_node = None
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        json_data = json.loads(decoded_line[6:])
                        agent_return = json_data.get('response')
                        if agent_return:
                            nodes = agent_return.get('nodes', {})
                            adjacency_list = agent_return.get('adj', {})
                            answer = agent_return.get('response', "")
                            if current_node != json_data.get('current_node'):
                                current_node = json_data.get('current_node')
                                logging.info(f"Agent: {mission['name']}-{current_node}")
                                logging.info(f"agent_return: {agent_return}")
            logging.info(f"Answer: {answer}")
            if len(answer)>300:
                newId = manager.update_markdown_to_notion(article["id"],answer,title=mission["name"])
                logging.critical(f"Inserted:{newId}{mission['name']} ")
            break
    except Exception as e:
        logging.error(f"Error: {e}")
        t.sleep(3600)
