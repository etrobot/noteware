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
                        "equals": "Mission"
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

    def markdown_to_notion_blocks(self, md_text):
        def create_heading_1(text):
            return {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                }
            }

        def create_heading_2(text):
            return {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                }
            }

        def create_heading_3(text):
            return {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                }
            }

        def create_bulleted_list_item(text):
            return {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                }
            }

        def create_numbered_list_item(text):
            return {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                }
            }

        def create_quote(text):
            return {
                "object": "block",
                "type": "quote",
                "quote": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                }
            }

        def create_paragraph(text):
            return {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": text}}]
                }
            }

        def create_link(text, href):
            return {
                "type": "text",
                "text": {
                    "content": text,
                    "link": {"url": href}
                }
            }

        def parse_paragraph(text):
            # 使用正则表达式查找所有的 [text](url) 形式的字符串
            pattern = re.compile(r'\[([^\]]+)\]\((http[^\)]+)\)')

            rich_text = []
            last_end = 0

            for match in pattern.finditer(text):
                start, end = match.span()
                if start > last_end:
                    # 处理普通文本部分
                    rich_text.append({"type": "text", "text": {"content": text[last_end:start]}})
                # 处理超链接部分
                link_text, link_url = match.groups()
                rich_text.append(create_link(link_text, link_url))
                last_end = end

            if last_end < len(text):
                # 处理剩余的普通文本部分
                rich_text.append({"type": "text", "text": {"content": text[last_end:]}})

            return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": rich_text}}

        blocks = []
        lines = md_text.split("\n")

        for line in lines:
            if len(line) == 0:
                continue
            if line.startswith("# "):
                blocks.append(create_heading_1(line[2:]))
            elif line.startswith("## "):
                blocks.append(create_heading_2(line[3:]))
            elif line.startswith("### "):
                blocks.append(create_heading_3(line[4:]))
            elif line.startswith("- "):
                blocks.append(create_bulleted_list_item(line[2:]))
            elif line.startswith("1. "):
                blocks.append(create_numbered_list_item(line[3:]))
            elif line.startswith("> "):
                blocks.append(create_quote(line[2:]))
            else:
                blocks.append(parse_paragraph(line))
        return blocks

    def insert_markdown_to_notion(self, md_text,title=None):
        blocks = []
        if title is None:
            title = md_text[:60]
            if len(md_text) > 100:
                blocks = self.markdown_to_notion_blocks(md_text)
        if len(blocks) > 0 and 'heading_1' in blocks[0]:
            title = blocks[0]['heading_1']['rich_text'][0]['text']['content']
        response = self.notion.pages.create(
            parent={"database_id": self.database_id},
            properties={
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                },
                "Status": {
                    "status": {
                        "name": "Draft"
                    }
                }
            },
            children=blocks
        )
        return response['id']
