import re
from collections import Counter
from sentiment_analysis.indonesian_sentiment_lexicon import POSITIVE_WORDS, NEGATIVE_WORDS, NEGATION_WORDS, CONTRAST_WORDS

def analyze_sentiment(text):
    text = text.lower()
    words = re.findall(r'\b\w+\b', text)
    word_counts = Counter(words)

    pos_count, neg_count = 0, 0
    negate = False 

    for i, word in enumerate(words):
        if word in NEGATION_WORDS:
            negate = True
            continue
        
        if word in POSITIVE_WORDS:
            pos_count += -1 if negate else 1
            negate = False  
        
        elif word in NEGATIVE_WORDS:
            neg_count += -1 if negate else 1
            negate = False  
            
    for word in words:
        if word in CONTRAST_WORDS:
            pos_count, neg_count = neg_count, pos_count 

    if pos_count > neg_count:
        sentiment = "positive"
    elif neg_count > pos_count:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return sentiment, pos_count, neg_count
