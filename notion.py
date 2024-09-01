import re
from notion_client import Client
import questionary

class NotionMarkdownManager:
    def __init__(self, api_key, database_id):
        self.notion = Client(auth=api_key)
        self.database_id = database_id

    def list_template_articles(self):
        response = self.notion.databases.query(
            **{
                "database_id": self.database_id,
                "filter": {
                    "property": "Status",
                    "status": {
                        "equals": "Misson"
                    }
                }
            }
        )
        articles = response.get('results', [])
        return articles

    def display_article_menu(self, articles):
        # Create a list of article titles with their corresponding IDs
        choices = [
            {"name": article["properties"]["Name"]["title"][0]["text"]["content"], "value": article["id"]}
            for article in articles
        ]

        # Create a selection menu using questionary
        answer = questionary.select(
            "Select an article to read:",
            choices=[choice["name"] for choice in choices]
        ).ask()

        # Find the selected article ID
        for choice in choices:
            if choice["name"] == answer:
                return choice["value"]

    def retrieve_block(self, block_id):
        return self.notion.blocks.retrieve(block_id)

    def retrieve_block_children(self, block_id):
        return self.notion.blocks.children.list(block_id)

    def parse_block(self, block):
        content = ""
        block_type = block['type']

        if block_type == 'paragraph':
            content += self.format_rich_text(block['paragraph']['rich_text']) + "\n\n"

        elif block_type == 'heading_1':
            content += "# " + self.format_rich_text(block['heading_1']['rich_text']) + "\n\n"

        elif block_type == 'heading_2':
            content += "## " + self.format_rich_text(block['heading_2']['rich_text']) + "\n\n"

        elif block_type == 'heading_3':
            content += "### " + self.format_rich_text(block['heading_3']['rich_text']) + "\n\n"

        elif block_type == 'bulleted_list_item':
            content += "- " + self.format_rich_text(block['bulleted_list_item']['rich_text']) + "\n"

        elif block_type == 'numbered_list_item':
            content += "1. " + self.format_rich_text(block['numbered_list_item']['rich_text']) + "\n"

        elif block_type == 'toggle':
            content += "<details>\n<summary>" + self.format_rich_text(block['toggle']['rich_text']) + "</summary>\n"
            if block['has_children']:
                children_blocks = self.retrieve_block_children(block['id'])
                for child_block in children_blocks['results']:
                    content += self.parse_block(child_block)
            content += "\n</details>\n"

        # Add more block types as needed

        if block['has_children'] and block_type not in ['toggle']:  # For blocks that aren't toggle
            children_blocks = self.retrieve_block_children(block['id'])
            for child_block in children_blocks['results']:
                content += self.parse_block(child_block)

        return content

    def format_rich_text(self, rich_text):
        text_content = ""
        for text in rich_text:
            annotations = text['annotations']
            plain_text = text['plain_text']

            if annotations['bold']:
                plain_text = f"**{plain_text}**"
            if annotations['italic']:
                plain_text = f"*{plain_text}*"
            if annotations['strikethrough']:
                plain_text = f"~~{plain_text}~~"
            if annotations['underline']:
                plain_text = f"<u>{plain_text}</u>"
            if annotations['code']:
                plain_text = f"`{plain_text}`"

            text_content += plain_text
        return text_content

    def get_article_content(self, page_id):
        response = self.notion.blocks.children.list(page_id)
        content = ""
        for block in response['results']:
            content += self.parse_block(block)
        return content


