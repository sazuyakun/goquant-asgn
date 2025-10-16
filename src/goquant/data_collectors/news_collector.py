"""Api endpoint to collect data from Newapi.org"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWSAPI_API_KEY")


def fetch_news(query, page_size=1):
    """
    Fetch news articles based on a query.
    """
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={NEWS_API_KEY}&pageSize={page_size}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


# if __name__ == "__main__":
#     OUTER_QUERY = "technology"
#     news_data = fetch_news(OUTER_QUERY)
#     print(news_data["articles"])

# Sample response:
# [{'source': {'id': None, 'name': 'Gizmodo.com'}, 'author': 'Margherita Bassi', 'title': 'Researchers Tested Bite-Resistant Wetsuit Material With Great Whites and Tiger Sharks. Here’s What Happened', 'description': 'Unlike zebra-striped wetsuits or chunky deterrent bracelets, this technology goes back to the basics.', 'url': 'https://gizmodo.com/researchers-tested-bite-resistant-wetsuit-material-with-great-whites-and-tiger-sharks-heres-what-happened-2000663459', 'urlToImage': 'https://gizmodo.com/app/uploads/2025/09/shark-biting-material-1200x675.jpg', 'publishedAt': '2025-09-25T13:45:07Z', 'content': 'Australian shark experts have revealed that some special wetsuit materials aiming to keep sharks from ripping your arm off or gouging out your guts might actually be helpful.\r\nAs detailed in a study … [+3265 chars]'}]
