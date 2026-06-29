import logging
import feedparser
import yfinance as yf
from datetime import datetime
from sqlalchemy.orm import Session
import asyncio
import aiohttp

from .models import Article
from .sentiment import analyze_sentiment
from .source_registry import get_all_feeds

logger = logging.getLogger(__name__)

# Headers to act like a real browser (as noted in source_registry.py)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

def ingest_yfinance_news(ticker: str, db: Session):
    """
    Fetches the latest news for a specific ticker using yfinance.
    Analyzes sentiment and stores in the DB.
    """
    logger.info(f"Fetching yfinance news for {ticker}...")
    try:
        stock = yf.Ticker(ticker)
        news = stock.news

        added_count = 0
        for item in news:
            url = item.get("link")
            title = item.get("title")

            # Check if article already exists
            existing = db.query(Article).filter(Article.url == url).first()
            if existing:
                continue

            # Analyze sentiment on the title (and summary if available)
            text_to_analyze = title
            summary = item.get("summary", "")
            if summary:
                text_to_analyze += " " + summary

            sentiment_result = analyze_sentiment(text_to_analyze)

            # Attempt to parse timestamp
            pub_date = datetime.utcnow()
            if "providerPublishTime" in item:
                pub_date = datetime.utcfromtimestamp(item["providerPublishTime"])

            article = Article(
                source="yfinance",
                ticker=ticker,
                title=title,
                url=url,
                content=summary,
                published_at=pub_date,
                sentiment_label=sentiment_result["label"],
                sentiment_score=sentiment_result["score"]
            )
            db.add(article)
            added_count += 1

        db.commit()
        logger.info(f"Added {added_count} new articles for {ticker} from yfinance.")
    except Exception as e:
        logger.error(f"Error fetching yfinance news for {ticker}: {e}")
        db.rollback()


async def fetch_and_parse_feed(session: aiohttp.ClientSession, feed_info: dict, db: Session):
    """
    Asynchronously fetches an RSS feed and stores new articles.
    """
    url = feed_info["rss_url"]
    source_name = feed_info["source_name"]
    category = feed_info.get("category", "Global")

    try:
        async with session.get(url, headers=HEADERS, timeout=15, allow_redirects=True) as resp:
            if resp.status != 200:
                logger.warning(f"Failed to fetch {url} (Status: {resp.status})")
                return

            text = await resp.text(errors="replace")
            parsed = feedparser.parse(text)

            added_count = 0
            for entry in parsed.entries[:5]: # Process top 5 to avoid overwhelming the free tier
                entry_url = entry.get("link")
                title = entry.get("title")

                if not entry_url or not title:
                    continue

                # Check DB
                existing = db.query(Article).filter(Article.url == entry_url).first()
                if existing:
                    continue

                summary = entry.get("summary", "")
                text_to_analyze = f"{title} {summary}"
                sentiment_result = analyze_sentiment(text_to_analyze)

                # Try to get published date
                pub_date = datetime.utcnow()
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        pub_date = datetime(*entry.published_parsed[:6])
                    except:
                        pass

                article = Article(
                    source=f"rss_{source_name}",
                    ticker=category, # Map category to ticker field for general news
                    title=title,
                    url=entry_url,
                    content=summary[:1000], # Store up to 1000 chars of summary
                    published_at=pub_date,
                    sentiment_label=sentiment_result["label"],
                    sentiment_score=sentiment_result["score"]
                )
                db.add(article)
                added_count += 1

            db.commit()
            if added_count > 0:
                logger.info(f"Added {added_count} new articles from {source_name}")

    except Exception as e:
        logger.error(f"Error processing feed {url}: {e}")
        db.rollback()


async def ingest_global_news_async(db: Session):
    """
    Orchestrates the fetching of all enabled RSS feeds from source_registry.
    """
    feeds = get_all_feeds(include_disabled=False)
    # To keep memory footprint low on the free tier, we limit the number of feeds we check per run
    # For a real deployment, you might want to paginate this or run different priorities at different schedules
    # Here, we'll take top 10 highest priority feeds to demonstrate.
    top_feeds = sorted(feeds, key=lambda x: x["priority"], reverse=True)[:10]

    logger.info(f"Starting ingestion for {len(top_feeds)} priority RSS feeds...")

    connector = aiohttp.TCPConnector(limit_per_host=2)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_and_parse_feed(session, feed, db) for feed in top_feeds]
        await asyncio.gather(*tasks)

    logger.info("Finished RSS feed ingestion.")


def ingest_global_news(db: Session):
    """Synchronous wrapper for the async global news ingestor."""
    asyncio.run(ingest_global_news_async(db))
