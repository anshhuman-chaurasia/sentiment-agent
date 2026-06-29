import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from pydantic import BaseModel
from typing import List, Optional

from .database import get_db, engine
from . import models
from .ingestion import ingest_yfinance_news, ingest_global_news

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Ensure tables are created
models.Base.metadata.create_all(bind=engine)

scheduler = BackgroundScheduler()

# --- Scheduler Jobs ---
def scheduled_ingestion():
    """Job to run periodically to fetch data."""
    logger.info("Starting scheduled ingestion job...")
    db = next(get_db())
    try:
        # Ingest major market stocks
        for ticker in ["AAPL", "TSLA", "NVDA", "SPY"]:
            ingest_yfinance_news(ticker, db)

        # Ingest global macro/sector news from RSS
        ingest_global_news(db)
    except Exception as e:
        logger.error(f"Error during scheduled ingestion: {e}")
    finally:
        db.close()
        logger.info("Finished scheduled ingestion job.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    logger.info("Starting up API and Scheduler...")
    # Run every 30 minutes
    scheduler.add_job(scheduled_ingestion, 'interval', minutes=30, id='main_ingestion_job')
    scheduler.start()
    yield
    # Shutdown event
    logger.info("Shutting down API and Scheduler...")
    scheduler.shutdown()

app = FastAPI(title="Stock Sentiment Agent API", lifespan=lifespan)


# --- API Models ---
class ArticleResponse(BaseModel):
    id: int
    source: str
    ticker: Optional[str]
    title: str
    url: str
    sentiment_label: Optional[str]
    sentiment_score: Optional[float]
    published_at: str

    class Config:
        from_attributes = True

class SentimentSummary(BaseModel):
    ticker: str
    average_score: float
    total_articles: int
    positive_count: int
    negative_count: int
    neutral_count: int


# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Stock Sentiment Agent API is running."}


@app.get("/api/articles", response_model=List[ArticleResponse])
def get_articles(ticker: Optional[str] = None, limit: int = 50, db: Session = Depends(get_db)):
    """Fetch stored articles, optionally filtered by ticker/category."""
    query = db.query(models.Article)
    if ticker:
        query = query.filter(models.Article.ticker == ticker.upper())
    articles = query.order_by(models.Article.published_at.desc()).limit(limit).all()

    # Format dates for response
    for a in articles:
        a.published_at = a.published_at.isoformat() if a.published_at else ""
    return articles


@app.get("/api/sentiment/{ticker}", response_model=SentimentSummary)
def get_sentiment_summary(ticker: str, db: Session = Depends(get_db)):
    """Get aggregated sentiment for a specific ticker/category."""
    articles = db.query(models.Article).filter(models.Article.ticker == ticker.upper()).all()

    if not articles:
        raise HTTPException(status_code=404, detail="No articles found for this ticker.")

    total = len(articles)
    scores = [a.sentiment_score for a in articles if a.sentiment_score is not None]

    pos = len([a for a in articles if a.sentiment_label == "positive"])
    neg = len([a for a in articles if a.sentiment_label == "negative"])
    neu = len([a for a in articles if a.sentiment_label == "neutral"])

    avg_score = sum(scores) / len(scores) if scores else 0.0

    return {
        "ticker": ticker.upper(),
        "average_score": avg_score,
        "total_articles": total,
        "positive_count": pos,
        "negative_count": neg,
        "neutral_count": neu
    }

@app.post("/api/ingest")
def trigger_ingestion(background_tasks: BackgroundTasks):
    """Manually trigger the ingestion process."""
    background_tasks.add_task(scheduled_ingestion)
    return {"message": "Ingestion job triggered in the background."}
