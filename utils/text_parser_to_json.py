import json
import re
from pathlib import Path


def parse_text_to_json(file_path: str) -> list[dict[str, str]]:
    text = Path(file_path).read_text(encoding="utf-8")

    # Split the text into individual article blocks.
    blocks = re.split(r"\n\s*\n", text.strip())

    articles = []

    for block in blocks:
        article = {}

        # Extract title, label, and content.
        for field in ("title", "label", "content"):
            pattern = rf"^{field}:\s*(.*?)(?=^(?:title|label|content):|\Z)"

            match = re.search(
                pattern,
                block,
                flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
            )

            if match:
                article[field] = match.group(1).strip()

        # Only include complete articles.
        if all(field in article for field in ("title", "label", "content")):
            articles.append(article)

    return articles


def save_as_json(articles: list[dict[str, str]], output_path: str) -> None:
    Path(output_path).write_text(
        json.dumps(articles, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )


def open_json_file(filename):
    with open(filename, "r", encoding="utf-8") as file:
        articles = json.load(file)

    return articles


if __name__ == "__main__":
    articles = parse_text_to_json("evaluation/articles.txt")
    save_as_json(articles, "data/articles.json")

    print(f"Parsed {len(articles)} articles.")

    with open("articles.json", "r", encoding="utf-8") as file:
        articles = json.load(file)

    m_count = 0
    nm_count = 0

    for article in articles:
        if article["label"] == "Major Event":
            m_count += 1
        elif article["label"] == "Non-Major Event":
            nm_count += 1

    print("Major Count: ", m_count)
    print("Non-Major Count: ", nm_count)
