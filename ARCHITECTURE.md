# Architecture Overview

This project is designed as an all-in-one AI agent that fetches financial/global news, performs sentiment analysis, and serves the results via an API and dashboard. It is optimized to run cost-effectively on an **Oracle Cloud Infrastructure (OCI) Always Free ARM Compute instance** (1 OCPU / 4GB RAM minimum).

## Diagram

```mermaid
graph TD
    subgraph "External Data Sources"
        YF[yfinance API]
        RSS[RSS Feeds (Source Registry)]
    end

    subgraph "OCI Always Free ARM Compute Instance"
        subgraph "Docker Compose"
            Agent[FastAPI + APScheduler Agent]
            DB[(SQLite / OCI Autonomous DB)]
            Dash[Streamlit Dashboard]
        end
    end

    YF -->|Stock News| Agent
    RSS -->|Global Sector News| Agent
    Agent <-->|Read/Write| DB
    Agent -- "HuggingFace\nFinBERT Pipeline" --> Agent
    Dash <-->|REST API| Agent
    User((User)) <-->|Web Browser\nHTTP 8501| Dash
```

## Components

1. **Data Ingestion (APScheduler)**:
   - Periodically runs background tasks (every 30 minutes).
   - Fetches specific ticker news via `yfinance`.
   - Iterates through a prioritized list of RSS feeds (e.g., Macro, Tech, Energy) defined in `app/source_registry.py`.
   - Deduplicates articles based on URL.

2. **Sentiment Analysis Layer**:
   - Utilizes Hugging Face's `transformers` library.
   - Runs the `ProsusAI/finbert` model, which is specifically trained on financial texts to classify sentiment as Positive, Negative, or Neutral.
   - Converts the textual classification into a normalized numeric score [-1.0, 1.0].

3. **Storage (SQLAlchemy)**:
   - Uses SQLite by default, mounted via a Docker volume for persistence across restarts.
   - Fully compatible with Oracle Autonomous Database (Always Free) by swapping the `DB_URL` environment variable.

4. **API (FastAPI)**:
   - Exposes RESTful endpoints (`/api/articles`, `/api/sentiment/{ticker}`) to access the processed data.
   - Allows manual triggering of the ingestion job.

5. **Frontend (Streamlit)**:
   - A lightweight web interface that reads from the API.
   - Displays real-time metrics, a sentiment breakdown chart, and an interactive data table of recent articles.