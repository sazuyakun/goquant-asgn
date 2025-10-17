"""Define the return types of different collectors"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, HttpUrl


# News article mode
class NewsSource(BaseModel):
    """Source of the news article"""

    id: Optional[str] = None
    name: str


class NewsArticle(BaseModel):
    """News article model"""

    source: NewsSource
    author: Optional[str] = None
    title: str
    description: Optional[str] = None
    url: HttpUrl
    urlToImage: Optional[HttpUrl] = None
    publishedAt: str
    content: Optional[str] = None


class NewsApiResponse(BaseModel):
    """Response model for News API"""

    status: str
    totalResults: int
    articles: List[NewsArticle]


# Reddit post model
class RedditPost(BaseModel):
    """Reddit post model"""

    title: str
    score: int
    url: HttpUrl
    num_comments: int
    created_utc: float


# Market data model
class MarketDataPoint(BaseModel):
    """Market data point model"""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
