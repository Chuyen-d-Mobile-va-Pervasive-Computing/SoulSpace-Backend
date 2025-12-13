"""
Auto-Train Toxic Detection Model
Automatically trains and saves models if they don't exist.
Run this script once, or integrate into FastAPI startup.
"""

import pickle
import re
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from scipy.sparse import hstack
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import nltk

# Ensure NLTK data is downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('wordnet')
    nltk.download('omw-1.4')

# ===========================
# Configuration
# ===========================
SCRIPT_DIR = Path(__file__).parent
DATA_FILE = SCRIPT_DIR / "train.csv"
MODELS_DIR = SCRIPT_DIR / "models"
LABEL_COLS = ['toxic', 'severe_toxic', 'obscene', 'threat', 'insult', 'identity_hate']

# Profanity patterns for preprocessing
PROFANITY_PATTERNS = [
    (r'f[\W_]*u[\W_]*c[\W_]*k', 'fuck'),
    (r'sh[\W_]*i[\W_]*t', 'shit'),
    (r'b[\W_]*i[\W_]*t[\W_]*c[\W_]*h', 'bitch'),
    (r'a[\W_]*s[\W_]*s[\W_]*h?[\W_]*o?[\W_]*l[\W_]*e?', 'asshole'),
    (r'd[\W_]*a[\W_]*m[\W_]*n', 'damn'),
    (r'h[\W_]*e[\W_]*l[\W_]*l', 'hell'),
]

CHAT_MAP = {
    r'\bu\b': 'you',
    r'\bur\b': 'your',
    r'\br\b': 'are',
}

POSITIVE_WORDS = [
    "good", "great", "awesome", "amazing", "nice", "cool", "fun", "funny",
    "love", "lovely", "beautiful", "perfect", "excellent", "fantastic"
]

positive_pattern = "|".join(POSITIVE_WORDS)
BENIGN_PROFANITY_PATTERN = re.compile(
    rf"\b(fucking|fuckin|fking|freaking)\s+({positive_pattern})\b",
    flags=re.IGNORECASE
)

lemmatizer = WordNetLemmatizer()


def normalize_text(text):
    """Normalize text for toxic detection"""
    if pd.isna(text):
        return ""
    
    text = str(text).lower()
    text = re.sub(r'<[^>]+>', ' ', text)  # Remove HTML
    text = BENIGN_PROFANITY_PATTERN.sub(lambda m: f"very {m.group(2)}", text)
    text = re.sub(r'@', 'a', text)
    text = re.sub(r'(.)\1{2,}', r'\1\1', text)
    
    for pattern, repl in PROFANITY_PATTERNS:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    
    for pattern, repl in CHAT_MAP.items():
        text = re.sub(pattern, repl, text)
    
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def custom_analyzer(text):
    """Custom analyzer for TF-IDF"""
    try:
        tokens = word_tokenize(text)
        return [lemmatizer.lemmatize(tok) for tok in tokens if tok.strip()]
    except:
        return text.split()


def check_models_exist():
    """Check if all model files exist"""
    required_files = ['lr_models.pkl', 'tfidf_word.pkl', 'tfidf_char.pkl']
    return all((MODELS_DIR / f).exists() for f in required_files)


def train_models():
    """Train and save toxic detection models"""
    print("=" * 60)
    print("🚀 Auto-Training Toxic Detection Model")
    print("=" * 60)
    
    # Check if data file exists
    if not DATA_FILE.exists():
        print(f"❌ Data file not found: {DATA_FILE}")
        print("   Please download train.csv from Kaggle Toxic Comment dataset")
        return False
    
    print(f"\n📂 Loading data from {DATA_FILE}...")
    df = pd.read_csv(DATA_FILE)
    print(f"   Loaded {len(df)} samples")
    
    # Preprocess
    print("\n🔧 Preprocessing text...")
    df['clean_text'] = df['comment_text'].apply(normalize_text)
    
    # TF-IDF Vectorizers
    print("\n📊 Building TF-IDF vectorizers...")
    
    print("   - Word n-grams (1-3)...")
    # Note: Using built-in 'word' analyzer instead of custom function
    # to avoid pickle serialization issues with module references
    tfidf_word = TfidfVectorizer(
        analyzer='word',  # Use built-in analyzer for pickle compatibility
        ngram_range=(1, 3),
        max_features=80000,
        min_df=3,
        max_df=0.9,
        sublinear_tf=True,
        token_pattern=r'\b\w+\b'  # Simple word tokenization
    )
    X_word = tfidf_word.fit_transform(df['clean_text'])
    print(f"     Shape: {X_word.shape}")
    
    print("   - Char n-grams (3-5)...")
    tfidf_char = TfidfVectorizer(
        analyzer='char',
        ngram_range=(3, 5),
        max_features=20000,
        min_df=3,
        max_df=0.9,
        sublinear_tf=True
    )
    X_char = tfidf_char.fit_transform(df['clean_text'])
    print(f"     Shape: {X_char.shape}")
    
    # Combine features
    X = hstack([X_word, X_char])
    print(f"\n📐 Combined feature shape: {X.shape}")
    
    # Train Logistic Regression for each label
    print("\n🤖 Training Logistic Regression models...")
    lr_models = {}
    
    for label in LABEL_COLS:
        print(f"   - Training {label}...", end=" ")
        y = df[label].values
        
        model = LogisticRegression(
            C=4.0,
            solver='lbfgs',
            max_iter=1000,
            n_jobs=-1
        )
        model.fit(X, y)
        lr_models[label] = model
        
        # Calculate positive ratio
        pos_ratio = y.sum() / len(y) * 100
        print(f"Done! (positive: {pos_ratio:.1f}%)")
    
    # Save models
    print("\n💾 Saving models...")
    MODELS_DIR.mkdir(exist_ok=True)
    
    with open(MODELS_DIR / 'lr_models.pkl', 'wb') as f:
        pickle.dump(lr_models, f)
    print("   ✓ lr_models.pkl saved")
    
    with open(MODELS_DIR / 'tfidf_word.pkl', 'wb') as f:
        pickle.dump(tfidf_word, f)
    print("   ✓ tfidf_word.pkl saved")
    
    with open(MODELS_DIR / 'tfidf_char.pkl', 'wb') as f:
        pickle.dump(tfidf_char, f)
    print("   ✓ tfidf_char.pkl saved")
    
    # Show file sizes
    print("\n📦 Model files:")
    total_size = 0
    for file in MODELS_DIR.glob('*.pkl'):
        size_mb = file.stat().st_size / (1024 * 1024)
        total_size += size_mb
        print(f"   - {file.name}: {size_mb:.2f} MB")
    print(f"   Total: {total_size:.2f} MB")
    
    print("\n" + "=" * 60)
    print("✅ Training completed successfully!")
    print("=" * 60)
    
    return True


def ensure_models_exist():
    """Ensure models exist, train if not"""
    if check_models_exist():
        print("✅ Toxic detection models already exist")
        return True
    else:
        print("⚠️ Models not found, starting auto-training...")
        return train_models()


if __name__ == "__main__":
    ensure_models_exist()
