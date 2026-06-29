import logging
from transformers import pipeline

logger = logging.getLogger(__name__)

# Try to load FinBERT, fallback to a simpler model if memory is an issue (though FinBERT is relatively small)
try:
    logger.info("Loading FinBERT sentiment analysis model...")
    # FinBERT is specialized for financial text
    sentiment_pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")
    logger.info("Model loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load FinBERT model: {e}")
    # Fallback to default
    logger.info("Loading default sentiment analysis model...")
    sentiment_pipeline = pipeline("sentiment-analysis")
    logger.info("Default model loaded successfully.")


def analyze_sentiment(text: str) -> dict:
    """
    Analyzes the sentiment of the provided text.
    Returns a dictionary with 'label' (positive/negative/neutral) and 'score'.
    """
    if not text:
        return {"label": "neutral", "score": 0.0}

    try:
        # The model might have a max token limit, so we truncate the text to the first ~500 words
        truncated_text = " ".join(text.split()[:500])
        result = sentiment_pipeline(truncated_text)[0]

        # Mapping labels depending on the model output
        label = result['label'].lower()
        score = result['score']

        # Adjust score to be between -1 and 1
        if label == "positive":
            mapped_score = score
        elif label == "negative":
            mapped_score = -score
        else:
            mapped_score = 0.0

        return {
            "label": label,
            "score": mapped_score
        }
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        return {"label": "neutral", "score": 0.0}
