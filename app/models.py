from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from .database import Base
from datetime import datetime

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, index=True) # e.g., "yfinance", "news_rss"
    ticker = Column(String, index=True, nullable=True) # Ticker if applicable, else general sector/macro
    title = Column(String)
    url = Column(String, unique=True, index=True)
    content = Column(Text, nullable=True)
    published_at = Column(DateTime, default=datetime.utcnow)

    # Sentiment analysis results
    sentiment_label = Column(String, nullable=True) # positive, negative, neutral
    sentiment_score = Column(Float, nullable=True) # Usually mapped -1 to 1 or 0 to 1 based on model

    created_at = Column(DateTime, default=datetime.utcnow)
