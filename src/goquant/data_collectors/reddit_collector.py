import os
from typing import List

import praw
from dotenv import load_dotenv

from goquant.data_collectors.base import BaseCollector
from goquant.data_collectors.models import RedditPost
from goquant.sentiment_analysis.text_preprocessor import TextPreprocessor

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
        self.preprocessor = TextPreprocessor()

    def fetch_data(
        self, query: str = "all", limit: int = 10, comment_limit: int = 20
    ) -> List[RedditPost]:
        """
        Fetch posts from the subreddit.
        """
        posts = []

        subreddit = self.reddit.subreddit(query)

        for post in subreddit.new(limit=limit):
            post.comments.replace_more(limit=0)

            comment_texts = []
            for comment in post.comments.list()[:comment_limit]:
                comment_texts.append(
                    {
                        "comment": comment.body,
                        "score": comment.score,
                    }
                )

            posts.append(
                {
                    "title": post.title,
                    "score": post.score,
                    "content": post.selftext,
                    "comments": comment_texts,
                    "url": post.url,
                    "num_comments": post.num_comments,
                    "created_utc": post.created_utc,
                }
            )

        return [RedditPost.model_validate(post) for post in posts]

    def preprocess_data(self, reddit_data: List[RedditPost]) -> List[RedditPost]:
        """
        Preprocess the Reddit posts' titles and content.
        """
        for post in reddit_data:
            post.title = self.preprocessor.preprocess(post.title)
            post.content = self.preprocessor.preprocess(post.content)
            for comment in post.comments:
                comment.comment = self.preprocessor.preprocess(comment.comment)
        return reddit_data
