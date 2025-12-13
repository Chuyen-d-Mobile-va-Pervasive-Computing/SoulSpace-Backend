"""
Toxic Content Detection Service - Integrated Version
Directly loads and uses the TF-IDF + Logistic Regression model.
No external Flask API required.
"""
import pickle
import re
from pathlib import Path
from typing import Optional
from pydantic import BaseModel


# ===========================
# Global Variables & Patterns (from Flask app)
# ===========================

# Profanity patterns
PROFANITY_PATTERNS = [
    (r'f[\W_]*u[\W_]*c[\W_]*k', 'fuck'),
    (r'sh[\W_]*i[\W_]*t', 'shit'),
    (r'b[\W_]*i[\W_]*t[\W_]*c[\W_]*h', 'bitch'),
    (r'a[\W_]*s[\W_]*s[\W_]*h?[\W_]*o?[\W_]*l[\W_]*e?', 'asshole'),
    (r'd[\W_]*a[\W_]*m[\W_]*n', 'damn'),
    (r'h[\W_]*e[\W_]*l[\W_]*l', 'hell'),
    (r'idi0t', 'idiot'),
    (r'st\*pid', 'stupid'),
]

# Chat lingo normalization
CHAT_MAP = {
    r'\bu\b': 'you',
    r'\bur\b': 'your',
    r'\br\b': 'are',
}

# Positive words for context-aware profanity normalization
POSITIVE_WORDS = [
    "good", "great", "awesome", "amazing", "nice",
    "cool", "fun", "funny", "love", "lovely", "beautiful",
    "perfect", "excellent", "fantastic", "wonderful", "brilliant",
    "superb", "outstanding", "impressive", "incredible", "fabulous",
    "terrific", "magnificent", "marvelous", "spectacular", "phenomenal",
    "cute", "sweet", "adorable", "delightful", "charming",
    "interesting", "exciting", "thrilling", "enjoyable", "pleasant",
    "happy", "glad", "joyful", "pleased", "satisfied",
    "best", "better", "top", "fine", "solid", "strong",
    "smart", "clever", "genius", "wise", "talented"
]

# Create regex patterns
positive_pattern = "|".join(POSITIVE_WORDS)
BENIGN_PROFANITY_PATTERN = re.compile(
    rf"\b(fucking|fuckin|fking|freaking)\s+({positive_pattern})\b",
    flags=re.IGNORECASE
)
INTENSIFIED_PATTERN = re.compile(
    rf"\b(so|really|very|pretty|quite)\s+(fucking|fuckin|fking)\s+({positive_pattern})\b",
    flags=re.IGNORECASE
)

# Label columns
LABEL_COLS = ['toxic', 'severe_toxic', 'obscene', 'threat', 'insult', 'identity_hate']


class ToxicPrediction(BaseModel):
    """Result from toxic content prediction"""
    text: str
    is_violation: bool
    label: str  # VIOLATION or CLEAN
    confidence: float
    toxic_labels: list[str] = []
    predictions: dict = {}


class ToxicDetectionService:
    """
    Service for detecting toxic/violation content.
    Directly loads and uses TF-IDF + Logistic Regression models.
    """
    
    def __init__(self, models_path: str = None, threshold: float = 0.5):
        self.threshold = threshold
        self.models_loaded = False
        self.lr_models = None
        self.tfidf_word = None
        self.tfidf_char = None
        self.lemmatizer = None
        
        # Determine models path
        if models_path is None:
            # Default: Only_Model/models relative to project root
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            self.models_path = project_root / "Only_Model" / "models"
            self.only_model_path = project_root / "Only_Model"
        else:
            self.models_path = Path(models_path).resolve()
            self.only_model_path = Path(models_path).resolve().parent
        
        # Try to load models
        self._load_models()
    
    def _check_models_exist(self) -> bool:
        """Check if all required model files exist"""
        required_files = ['lr_models.pkl', 'tfidf_word.pkl', 'tfidf_char.pkl']
        return all((self.models_path / f).exists() for f in required_files)
    
    def _auto_train(self) -> bool:
        """Automatically train models if train.csv exists"""
        try:
            # Check if auto_train.py exists
            auto_train_script = self.only_model_path / "auto_train.py"
            train_csv = self.only_model_path / "train.csv"
            
            if not train_csv.exists():
                print(f"   ❌ Training data not found: {train_csv}")
                return False
            
            if not auto_train_script.exists():
                print(f"   ❌ Auto-train script not found: {auto_train_script}")
                return False
            
            print("   🚀 Starting auto-training (this may take a few minutes)...")
            
            # Use importlib to dynamically import auto_train
            import sys
            import importlib.util
            
            spec = importlib.util.spec_from_file_location("auto_train", str(auto_train_script))
            auto_train_module = importlib.util.module_from_spec(spec)
            sys.modules["auto_train"] = auto_train_module
            spec.loader.exec_module(auto_train_module)
            
            result = auto_train_module.ensure_models_exist()
            
            # Cleanup
            del sys.modules["auto_train"]
            
            return result
            
        except Exception as e:
            print(f"   ❌ Auto-train failed: {e}")
            return False
    
    def _load_models(self):
        """Load trained models and vectorizers. Auto-train if not exist."""
        try:
            # Check if models exist, if not try to auto-train
            if not self.models_path.exists() or not self._check_models_exist():
                print(f"⚠️ Toxic models not found at: {self.models_path}")
                
                # Try auto-train
                if self._auto_train():
                    print("✅ Auto-training completed!")
                else:
                    print("   Models not available. Posts will be approved without AI scan.")
                    return
            
            # Lazy imports - only import when loading models
            from nltk.stem import WordNetLemmatizer
            from scipy.sparse import hstack
            self._hstack = hstack  # Store for later use
            
            # Load models
            with open(self.models_path / 'lr_models.pkl', 'rb') as f:
                self.lr_models = pickle.load(f)
            
            # Load vectorizers
            with open(self.models_path / 'tfidf_word.pkl', 'rb') as f:
                self.tfidf_word = pickle.load(f)
            
            with open(self.models_path / 'tfidf_char.pkl', 'rb') as f:
                self.tfidf_char = pickle.load(f)
            
            # Initialize lemmatizer
            self.lemmatizer = WordNetLemmatizer()
            
            self.models_loaded = True
            print("✅ Toxic detection models loaded successfully!")
            
        except FileNotFoundError as e:
            print(f"⚠️ Toxic model files not found: {e}")
            print("   Run: cd Only_Model && python save_models.py")
        except Exception as e:
            import traceback
            print(f"❌ Error loading toxic models: {e}")
            traceback.print_exc()
    
    def _normalize_for_toxic(self, text: str) -> str:
        """Normalize text for toxic detection"""
        # Lowercase
        text = text.lower()
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Replace benign profanity with intensifiers
        text = INTENSIFIED_PATTERN.sub(lambda m: f"{m.group(1)} very {m.group(3)}", text)
        text = BENIGN_PROFANITY_PATTERN.sub(lambda m: f"very {m.group(2)}", text)
        
        # Normalize leet speak: @ → a
        text = re.sub(r'@', 'a', text)
        
        # Collapse repeated characters
        text = re.sub(r'(.)\1{2,}', r'\1\1', text)
        
        # Collapse repeated punctuation
        text = re.sub(r'!{2,}', '!', text)
        text = re.sub(r'\?{2,}', '?', text)
        text = re.sub(r'\.{2,}', '.', text)
        
        # Normalize obfuscated profanity
        for pattern, repl in PROFANITY_PATTERNS:
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
        
        # Normalize chat lingo
        for pattern, repl in CHAT_MAP.items():
            text = re.sub(pattern, repl, text)
        
        # Remove extra whitespaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _predict_toxicity(self, text: str) -> tuple[dict, str]:
        """Predict toxicity for given text"""
        # Normalize text
        normalized = self._normalize_for_toxic(text)
        
        # Vectorize
        vec_word = self.tfidf_word.transform([normalized])
        vec_char = self.tfidf_char.transform([normalized])
        vec = self._hstack([vec_word, vec_char])
        
        # Predict
        predictions = {}
        for label in LABEL_COLS:
            prob = self.lr_models[label].predict_proba(vec)[0, 1]
            predictions[label] = float(prob)
        
        return predictions, normalized
    
    async def check_health(self) -> bool:
        """Check if toxic detection models are loaded"""
        return self.models_loaded
    
    async def analyze_text(self, text: str, threshold: Optional[float] = None) -> ToxicPrediction:
        """
        Analyze text for toxic content.
        
        Args:
            text: The text to analyze
            threshold: Classification threshold (default: 0.5)
        
        Returns:
            ToxicPrediction with violation status and details
        """
        threshold = threshold or self.threshold
        
        if not self.models_loaded:
            # Models not loaded - return safe default
            return ToxicPrediction(
                text=text,
                is_violation=False,
                label="NOT_LOADED",
                confidence=0.0,
                toxic_labels=[],
                predictions={}
            )
        
        try:
            predictions, normalized = self._predict_toxicity(text)
            
            # Determine toxicity
            toxic_labels = [label for label, prob in predictions.items() if prob > threshold]
            is_toxic = len(toxic_labels) > 0
            
            # Find max toxicity
            max_label = max(predictions.items(), key=lambda x: x[1])
            
            return ToxicPrediction(
                text=text,
                is_violation=is_toxic,
                label="VIOLATION" if is_toxic else "CLEAN",
                confidence=max_label[1],
                toxic_labels=toxic_labels,
                predictions=predictions
            )
            
        except Exception as e:
            print(f"Toxic analysis error: {e}")
            return ToxicPrediction(
                text=text,
                is_violation=False,
                label="ERROR",
                confidence=0.0,
                toxic_labels=[],
                predictions={}
            )
    
    async def analyze_batch(self, texts: list[str], threshold: Optional[float] = None) -> dict:
        """
        Analyze multiple texts for toxic content.
        
        Args:
            texts: List of texts to analyze (max 100)
            threshold: Classification threshold
        
        Returns:
            Dict with results and summary
        """
        threshold = threshold or self.threshold
        
        results = []
        toxic_count = 0
        
        for text in texts[:100]:
            result = await self.analyze_text(text, threshold)
            
            if result.is_violation:
                toxic_count += 1
            
            results.append({
                "text": text,
                "is_violation": result.is_violation,
                "label": result.label,
                "confidence": result.confidence,
                "toxic_labels": result.toxic_labels
            })
        
        return {
            "results": results,
            "summary": {
                "total": len(texts),
                "toxic": toxic_count,
                "clean": len(texts) - toxic_count,
                "toxic_percentage": round(toxic_count / len(texts) * 100, 2) if texts else 0
            },
            "threshold": threshold
        }


# Singleton instance
_toxic_service: Optional[ToxicDetectionService] = None


def get_toxic_detection_service() -> ToxicDetectionService:
    """Get or create toxic detection service instance"""
    global _toxic_service
    if _toxic_service is None:
        _toxic_service = ToxicDetectionService()
    return _toxic_service
