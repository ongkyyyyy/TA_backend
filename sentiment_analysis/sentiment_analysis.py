import re
from collections import Counter
from sentiment_analysis.indonesian_sentiment_lexicon import POSITIVE_WORDS, NEGATIVE_WORDS

def analyze_sentiment(text):
    """Lexicon-based sentiment analysis for Indonesian hotel reviews."""
    text = text.lower()  
    words = re.findall(r'\b\w+\b', text)  
    word_counts = Counter(words)

    pos_count = sum(word_counts[word] for word in word_counts if word in POSITIVE_WORDS)
    neg_count = sum(word_counts[word] for word in word_counts if word in NEGATIVE_WORDS)

    if pos_count > neg_count:
        sentiment = "positive"
    elif neg_count > pos_count:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return sentiment, pos_count, neg_count 
