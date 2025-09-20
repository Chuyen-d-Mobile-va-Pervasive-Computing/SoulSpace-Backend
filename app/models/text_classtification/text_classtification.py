"""
Text safety classification and rule-based lexicon checker.

This module is written for high maintainability and contains:

- preprocessing utilities for Vietnamese text (cleaning + tokenization hooks)
- lexicon loader (CSV file and optional MongoDB loader)
- rule-based scorer that uses a negative lexicon with weights
- skeleton for PhoBERT + Attention model integration (lazy import / device-safe)
- hybrid checker that combines rule-based and DL model scores

Notes about data (high maintenance):
- Shipping lexicon: keep a CSV at `safety_checker/data/negative_lexicon.csv` or
  store lexicon entries in MongoDB in a collection named `negative_lexicon`.
- If using MongoDB, this repo already exposes `app.core.database.client` and
  `app.core.config.settings` where `settings.MONGO_URI` and
  `settings.DATABASE_NAME` are defined. Use `init_db()` at application start
  (see `app.core.database.init_db`). We provide `load_lexicon_from_mongo`
  below which uses the same Motor client.

Maintenance guidelines:
- Keep pure-Python rule-based logic small and well-tested (unit tests cover it).
- Keep model-loading lazy. Loading transformer models is expensive; call
  `load_dl_model()` once at app startup and pass the returned object to the
  API handlers (or store on FastAPI "app.state").

Example usage:
    from app.models.text_classtification.text_classtification import (
        preprocess_text, load_lexicon_from_csv, rule_based_scoring, hybrid_safety_check
    )

    text = "Mày là đồ ngu, cút khỏi đây đi"
    tokens = preprocess_text(text)
    lex = load_lexicon_from_csv('safety_checker/data/negative_lexicon.csv')
    result = rule_based_scoring(tokens, lex)

The functions return simple, JSON-serializable dicts to plug directly into an API.
"""

from typing import Dict, List, Tuple, Optional
import re
import csv
import logging
from pathlib import Path

# Lazy imports for optional dependencies (transformers/torch)
_HAS_TRANSFORMERS = False
try:
    import torch
    from transformers import AutoTokenizer, AutoModel
    _HAS_TRANSFORMERS = True
except Exception:
    # Not critical for rule-based checks. Models are optional and loaded lazily.
    pass

logger = logging.getLogger(__name__)


# -------------------------------
# Preprocessing utilities
# -------------------------------

def normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def preprocess_text(text: str, keep_punct: bool = False) -> str:
    """Simple, high-maintenance-friendly text normalizer.

    - Removes URLs
    - Removes control characters
    - Optionally strips most punctuation (defaults to keep basic .,!? for
      readability but downstream tokenizers like PhoBERT may expect segmented text)

    IMPORTANT: For Vietnamese transformer models (PhoBERT), the text should be
    tokenized/segmented according to the model's requirements (word segmentation).
    Use `underthesea` or `VnCoreNLP` externally and feed the segmented text here
    if your model requires it.
    """
    if not text:
        return ""

    # remove urls
    text = re.sub(r"http\S+|www\.[^\s]+", "", text)

    # remove control chars
    text = re.sub(r"[\r\t\n]+", " ", text)

    if not keep_punct:
        # keep letters, numbers and basic punctuation . , ! ? and spaces.
        # Avoid \p{L} which isn't supported by Python's `re` module. We allow
        # word characters (unicode aware) plus the common Vietnamese diacritics
        # by permitting any letter-like characters via the Unicode category
        # shortcut "\w" and an explicit whitelist for punctuation.
        # This is intentionally permissive; downstream tokenizers should be
        # preferred for exact segmentation.
        text = re.sub(r"[^\w\s\.,!\?\-']", " ", text, flags=re.UNICODE)

    text = normalize_whitespace(text)

    return text


# -------------------------------
# Lexicon loading (CSV + MongoDB)
# -------------------------------

def load_lexicon_from_csv(path: str) -> Dict[str, float]:
    """Load negative lexicon CSV with columns: word,weight[,category]

    Returns a dict mapping normalized token -> weight (float).
    """
    lex: Dict[str, float] = {}
    p = Path(path)
    if not p.exists():
        logger.warning("Lexicon CSV not found: %s", path)
        return lex

    with p.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            word = row.get("word") or row.get("token")
            w = row.get("weight") or row.get("score") or "0"
            if not word:
                continue
            try:
                weight = float(w)
            except Exception:
                weight = 0.0
            lex[word.strip()] = weight

    return lex


def load_lexicon_from_mongo(db, collection_name: str = "negative_lexicon") -> Dict[str, float]:
    """Load lexicon from a MongoDB collection.

    Expected document shape in collection:
        { "word": "cút đi", "weight": 0.18, "category": "insult" }

    Notes:
    - `db` is an AsyncIOMotorDatabase or similar. This function is synchronous
      for simplicity; in async contexts, use an async loader that awaits the
      cursor. Here we assume calling code will convert to list() as needed.
    - Using Mongo allows updating lexicon at runtime without redeploy.
    """
    lex: Dict[str, float] = {}
    try:
        # If db is motor async database, it returns an AsyncIOMotorCollection.
        # We'll attempt to read synchronously if it's a pymongo-like DB, otherwise
        # the caller should implement async reading.
        if hasattr(db, "find"):
            # Attempt to iterate (works for pymongo)
            cursor = db[collection_name].find({})
            # If this is Motor's async cursor, it will be awaitable. We don't
            # attempt to await here; prefer the caller use an async helper.
            if hasattr(cursor, "to_list"):
                # motor async cursor: don't block here; raise informative error
                raise RuntimeError(
                    "Async motor cursor detected: use `load_lexicon_from_mongo_async` instead."
                )
            for doc in cursor:
                word = doc.get("word")
                weight = doc.get("weight", 0.0)
                if word:
                    try:
                        lex[word] = float(weight)
                    except Exception:
                        lex[word] = 0.0
    except Exception as e:
        logger.exception("Error loading lexicon from mongo: %s", e)

    return lex


async def load_lexicon_from_mongo_async(db, collection_name: str = "negative_lexicon") -> Dict[str, float]:
    """Async loader for Motor (recommended if using Motor client).

    Example usage in FastAPI startup event:
        from app.core.database import client
        db = client[settings.DATABASE_NAME]
        lex = await load_lexicon_from_mongo_async(db)
    """
    lex: Dict[str, float] = {}
    try:
        cursor = db[collection_name].find({})
        docs = await cursor.to_list(length=None)
        for doc in docs:
            word = doc.get("word")
            weight = doc.get("weight", 0.0)
            if word:
                try:
                    lex[word] = float(weight)
                except Exception:
                    lex[word] = 0.0
    except Exception as e:
        logger.exception("Error loading lexicon from mongo async: %s", e)

    return lex


# -------------------------------
# Rule-based scoring
# -------------------------------

def rule_based_scoring(tokenized_text: str, lexicon: Dict[str, float], max_penalty: float = 1.0) -> Dict:
    """Score text using lexicon weights.

    Inputs:
    - tokenized_text: string where tokens are separated by whitespace (e.g., from
      underthesea word_tokenize output).
    - lexicon: dict token -> weight. Tokens should match tokenization.

    Returns a dict with keys: is_violation, safety_score, violation_words, penalty
    """
    if not tokenized_text:
        return {"is_violation": False, "safety_score": 1.0, "violation_words": [], "penalty": 0.0}

    tokens = tokenized_text.split()
    violation_words: List[str] = []
    total_penalty = 0.0

    # Matching strategy: exact token match; projects may implement fuzzy matching
    # or normalized forms (stem/lemma) if needed.
    for token in tokens:
        if token in lexicon:
            violation_words.append(token)
            total_penalty += float(lexicon[token])

    # Cap penalty
    total_penalty = min(total_penalty, float(max_penalty))

    safety_score = max(0.0, 1.0 - total_penalty)

    return {
        "is_violation": len(violation_words) > 0,
        "safety_score": round(safety_score, 4),
        "violation_words": violation_words,
        "penalty": round(total_penalty, 4),
    }


# -------------------------------
# Deep Learning model skeleton (PhoBERT + Attention)
# -------------------------------

class PhoBERTWithAttentionWrapper:
    """Lightweight wrapper to lazily load a PhoBERT model with a simple
    attention pooling + regression head.

    Usage:
        model_wrapper = PhoBERTWithAttentionWrapper('vinai/phobert-base')
        model_wrapper.load(device='cpu')
        score, tokens, attn = model_wrapper.predict(text)

    Notes on maintenance:
    - Keep weights and tokenizer paths configurable via settings.
    - Loading is expensive; store the wrapper instance on FastAPI app.state.
    """

    def __init__(self, model_name: str = "vinai/phobert-base", max_len: int = 128):
        if not _HAS_TRANSFORMERS:
            raise RuntimeError("transformers and torch are required for DL model functionality")

        self.model_name = model_name
        self.max_len = max_len
        self.device = "cpu"
        self.tokenizer = None
        self.model = None

    def load(self, device: Optional[str] = None):
        """Load tokenizer and model into memory. Call once at startup.

        device: 'cpu' or 'cuda' or None (auto-detect)
        """
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        # We load AutoModel and add a tiny attention/regression head at runtime
        base = AutoModel.from_pretrained(self.model_name)

        # Attach a small regression head + attention; keep it simple so users can
        # replace with a persisted fine-tuned model later.
        class ModelWithHead(torch.nn.Module):
            def __init__(self, base_model):
                super().__init__()
                self.base = base_model
                hidden = base_model.config.hidden_size
                self.attn = torch.nn.Linear(hidden, 1)
                self.dropout = torch.nn.Dropout(0.2)
                self.regressor = torch.nn.Linear(hidden, 1)

            def forward(self, input_ids, attention_mask):
                outputs = self.base(input_ids=input_ids, attention_mask=attention_mask)
                last = outputs.last_hidden_state  # (batch, seq, hidden)
                attn_weights = torch.tanh(self.attn(last))  # (batch, seq, 1)
                attn_weights = torch.softmax(attn_weights, dim=1)
                context = torch.sum(attn_weights * last, dim=1)  # (batch, hidden)
                x = self.dropout(context)
                out = self.regressor(x)
                out = torch.sigmoid(out).squeeze(-1)
                return out, attn_weights

        self.model = ModelWithHead(base).to(self.device)
        self.model.eval()

    def predict(self, text: str, top_k_tokens: int = 3) -> Dict:
        """Return safety score and top tokens by attention.

        Returns dict: { 'safety_score': float, 'violation_tokens': List[str], 'attention': List[float] }
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        # Note: For Vietnamese, the text should be segmented externally (underthesea)
        encoding = self.tokenizer.encode_plus(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_len,
            return_tensors='pt',
            return_attention_mask=True,
        )
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)

        with torch.no_grad():
            score_tensor, attn_weights = self.model(input_ids, attention_mask)

        safety_score = float(score_tensor.cpu().numpy().item())

        # Convert attention and tokens to python objects
        attn = attn_weights.squeeze(-1).squeeze(0).cpu().numpy()  # (seq_len,)
        ids = input_ids.squeeze(0).cpu().numpy()
        tokens = self.tokenizer.convert_ids_to_tokens(ids)

        # select top-k tokens by attention weight (ignore special tokens)
        import numpy as _np

        idxs = _np.argsort(attn)[-top_k_tokens:][::-1]
        violation_tokens = []
        for i in idxs:
            tok = tokens[i]
            if tok in [self.tokenizer.pad_token, self.tokenizer.cls_token, self.tokenizer.sep_token]:
                continue
            violation_tokens.append(tok)

        return {"safety_score": round(safety_score, 4), "violation_tokens": violation_tokens, "attention": attn.tolist()}


# -------------------------------
# Hybrid checker combining rule-based + DL
# -------------------------------

def hybrid_safety_check(tokenized_text: str, lexicon: Dict[str, float], dl_wrapper: Optional[PhoBERTWithAttentionWrapper] = None, threshold: float = 0.5) -> Dict:
    """Combine rule-based and optional DL model to return final decision.

    - If lexicon penalty is very high, return rule-based result immediately.
    - If DL wrapper provided, compute DL score and combine with weighted average.
    """
    rule = rule_based_scoring(tokenized_text, lexicon)

    # fast path: strong rule-based penalty
    if rule["penalty"] >= 0.6:
        return {**rule, "method": "rule-based"}

    dl_result = None
    if dl_wrapper is not None:
        # dl_wrapper expects raw text segmented appropriately
        try:
            dl_result = dl_wrapper.predict(tokenized_text)
        except Exception:
            logger.exception("Error running DL model; falling back to rule-based only.")
            dl_result = None

    if dl_result is None:
        return {**rule, "method": "rule-based"}

    final_score = round(0.3 * rule["safety_score"] + 0.7 * dl_result["safety_score"], 4)
    is_violation = final_score < threshold

    combined_violations = list(dict.fromkeys(rule.get("violation_words", []) + dl_result.get("violation_tokens", [])))

    return {
        "is_violation": is_violation,
        "safety_score": final_score,
        "violation_words": combined_violations,
        "method": "hybrid",
        "rule_score": rule["safety_score"],
        "dl_score": dl_result["safety_score"],
    }


# -------------------------------
# Small CLI / test helpers
# -------------------------------

if __name__ == "__main__":
    # Quick demonstration when run directly (keeps file self-contained for dev)
    sample = "đm tụi mày muốn bị bắn à!"
    print("Original:", sample)
    processed = preprocess_text(sample)
    print("Processed:", processed)
    # Resolve the data directory relative to repository root: safety_checker/data
    # File layout: app/models/text_classtification/<this file>
    # - parents[2] -> app/models
    # - parents[3] -> app
    # We want to get to repository root and then safety_checker/data
    repo_root = Path(__file__).resolve().parents[3]
    # Preferred central data directory (created earlier): <repo>/safety_checker/data
    central = repo_root / "safety_checker" / "data" / "negative_lexicon.csv"
    # Module-local fallback: app/models/text_classtification/data/negative_lexicon.csv
    local = Path(__file__).resolve().parent / "data" / "negative_lexicon.csv"
    # Also check the legacy/mistyped path (was present in file): <repo>/models/safety_checker/data
    alt = repo_root / "models" / "safety_checker" / "data" / "negative_lexicon.csv"
    # Also check the nested safety_checker under this module (found in repo):
    module_nested = Path(__file__).resolve().parent / "safety_checker" / "data" / "negative_lexicon.csv"

    # Choose the first path that exists (central preferred)
    if central.exists():
        csv_path = central
    elif local.exists():
        csv_path = local
    elif module_nested.exists():
        csv_path = module_nested
    elif alt.exists():
        csv_path = alt
    else:
        # Default to central (may not exist) so load_lexicon_from_csv will warn
        csv_path = central
    lex = {}
    if csv_path.exists():
        # log which path we picked so maintainers can debug
        print("Using lexicon file:", str(csv_path))
        lex = load_lexicon_from_csv(str(csv_path))
    else:
        # Small default lexicon for quick dev testing
        lex = {"ngu": 0.1, "cút": 0.18, "cút khỏi đây": 0.18}

    print("Lexicon sample:", list(lex.items())[:5])
    print("Rule-based result:", rule_based_scoring(processed, lex))
