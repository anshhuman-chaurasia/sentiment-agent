# Usage Guide

Once the Stock Sentiment Agent is deployed and running, you have two primary ways to interact with it:

## 1. Streamlit Dashboard

The easiest way to view insights is through the Streamlit UI, available at `http://<YOUR_IP>:8501`.

- **Sentiment Summary:** In the left sidebar, enter a specific ticker (e.g., `TSLA`) or a sector category (e.g., `Macro`) and click "Get Summary". This calculates the average sentiment score based on the historical data in the database.
- **Manual Ingestion:** By default, the system scrapes news every 30 minutes. If you want to force an immediate update, click "Trigger Ingestion" in the sidebar. The scraping and ML inference will run in the background.
- **Recent Articles:** Scroll down to see the latest articles fetched by the system. The table is color-coded based on sentiment (Green for positive, Red for negative). You can filter this table by typing a ticker or sector name.

## 2. REST API

The underlying system is a FastAPI application running on `http://<YOUR_IP>:8000`. You can integrate these endpoints into other tools, scripts, or Oracle Analytics Cloud.

View the interactive Swagger UI at `http://<YOUR_IP>:8000/docs`.

### Key Endpoints

- **`GET /api/articles`**
  - **Query Params:** `limit` (int, default=50), `ticker` (string, optional)
  - **Returns:** A list of recent articles with their titles, URLs, publication dates, and calculated sentiment scores.

- **`GET /api/sentiment/{ticker}`**
  - **Path Param:** `ticker` (string)
  - **Returns:** A summary JSON object containing `average_score`, `total_articles`, `positive_count`, `negative_count`, and `neutral_count`.

- **`POST /api/ingest`**
  - **Returns:** Triggers the background scheduler immediately. Useful if you've added new RSS feeds to the code and want to test them without waiting for the next cron interval.

## Adding New Sources

To add new global news sources, edit `app/source_registry.py`. The `ingestion.py` script automatically reads the enabled feeds from the registry during its scheduled runs. Make sure the feeds return valid XML/RSS.