import re
from collections import Counter
from sentiment_analysis.indonesian_sentiment_lexicon import NEGATION_WORDS, CONTRAST_WORDS

def load_words_from_txt(path):
    with open(path, 'r', encoding='utf-8') as file:
        return set(line.strip().lower() for line in file if line.strip())

POSITIVE_WORDS = load_words_from_txt('sentiment_analysis/positive.txt')
NEGATIVE_WORDS = load_words_from_txt('sentiment_analysis/negative.txt')

def analyze_sentiment(text):
    text = text.lower()
    words = re.findall(r'\b\w+\b', text)

    pos_count = sum(1 for word in words if word in POSITIVE_WORDS)
    neg_count = sum(1 for word in words if word in NEGATIVE_WORDS)

    if pos_count > neg_count:
        sentiment = "positive"
    elif neg_count > pos_count:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return sentiment, pos_count, neg_count
