import os
from typing import List

import praw
from dotenv import load_dotenv

from goquant.data_collectors.base import BaseCollector
from goquant.data_collectors.models import RedditPost

load_dotenv()


class RedditCollector(BaseCollector):
    """
    Collector for Reddit data.
    """

    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT"),
        )

    def fetch_data(self, query: str = "all", limit: int = 10) -> List[RedditPost]:
        """
        Fetch posts from the subreddit.
        """
        posts = []
        for post in self.reddit.subreddit(query).hot(limit=limit):
            posts.append(
                {
                    "title": post.title,
                    "score": post.score,
                    "url": post.url,
                    "num_comments": post.num_comments,
                    "created_utc": post.created_utc,
                }
            )
        return [RedditPost.model_validate(post) for post in posts]
