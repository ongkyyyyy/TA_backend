
import re
import joblib
import pandas as pd
from sentiment_analysis.indonesian_sentiment_lexicon import NEGATION_WORDS, CONTRAST_WORDS

def load_words_from_txt(path):
    with open(path, 'r', encoding='utf-8') as file:
        return set(line.strip().lower() for line in file if line.strip())

POSITIVE_WORDS = load_words_from_txt('sentiment_analysis/positive.txt')
NEGATIVE_WORDS = load_words_from_txt('sentiment_analysis/negative.txt')

MODEL = joblib.load('sentiment_analysis/sentiment_model.pkl')

def extract_features(text):
    text = text.lower()
    words = re.findall(r'\b\w+\b', text)

    pos_count = sum(1 for word in words if word in POSITIVE_WORDS)
    neg_count = sum(1 for word in words if word in NEGATIVE_WORDS)
    has_negation = any(word in NEGATION_WORDS for word in words)
    has_contrast = any(word in CONTRAST_WORDS for word in words)
    word_count = len(words)

    return {
        "pos_count": pos_count,
        "neg_count": neg_count,
        "has_negation": int(has_negation),
        "has_contrast": int(has_contrast),
        "word_count": word_count
    }

def analyze_sentiment(text):
    features = extract_features(text)
    df = pd.DataFrame([features])
    sentiment = MODEL.predict(df)[0]
    return sentiment, features["pos_count"], features["neg_count"]
