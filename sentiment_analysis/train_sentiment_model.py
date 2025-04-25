import pandas as pd
import re
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from scipy.sparse import hstack
import joblib

# Optional: Uncomment if using SMOTE
from imblearn.over_sampling import SMOTE

# Load sentiment word lists
def load_words_from_txt(path):
    with open(path, 'r', encoding='utf-8') as file:
        return set(line.strip().lower() for line in file if line.strip())

POSITIVE_WORDS = load_words_from_txt('sentiment_analysis/positive.txt')
NEGATIVE_WORDS = load_words_from_txt('sentiment_analysis/negative.txt')
NEGATION_WORDS = {"tidak", "bukan", "jangan", "tanpa"}
CONTRAST_WORDS = {"tetapi", "namun", "meskipun", "walaupun"}

# Extract lexical features
def extract_features(text):
    text = text.lower()
    words = re.findall(r'\b\w+\b', text)
    return {
        "pos_count": sum(word in POSITIVE_WORDS for word in words),
        "neg_count": sum(word in NEGATIVE_WORDS for word in words),
        "has_negation": int(any(word in NEGATION_WORDS for word in words)),
        "has_contrast": int(any(word in CONTRAST_WORDS for word in words)),
        "word_count": len(words)
    }

# Load data
df = pd.read_csv("sentiment_analysis/labeled_reviews.csv")
df.dropna(subset=["review", "label"], inplace=True)

# Extract features
lexical_features = df["review"].apply(extract_features).apply(pd.Series)

# TF-IDF Vectorization
tfidf = TfidfVectorizer(ngram_range=(1, 2), max_features=3000)
tfidf_features = tfidf.fit_transform(df["review"])

# Combine TF-IDF + Lexical features
from numpy import array
X_combined = hstack([tfidf_features, array(lexical_features)])
y = df["label"]

# Optional: Handle imbalanced dataset
smote = SMOTE(random_state=42)
X_combined, y = smote.fit_resample(X_combined, y)

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X_combined, y, test_size=0.2, stratify=y, random_state=42)

# Train model
clf = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
clf.fit(X_train, y_train)

# Evaluate
y_pred = clf.predict(X_test)
print(classification_report(y_test, y_pred))

# Save model and vectorizer
joblib.dump(clf, "sentiment_analysis/sentiment_model.pkl")
joblib.dump(tfidf, "sentiment_analysis/tfidf_vectorizer.pkl")
