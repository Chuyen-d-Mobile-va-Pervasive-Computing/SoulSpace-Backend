"""
AI Sentiment Analysis API endpoint.
Allows direct access to sentiment analysis functionality.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

# Import the shared sentiment analysis function
from app.services.user.journal_service import analyze_sentiment

router = APIRouter(prefix="/ai", tags=["🤖 AI - Analysis"])


class SentimentRequest(BaseModel):
    """Request body for sentiment analysis"""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to analyze")


class SentimentResponse(BaseModel):
    """Response from sentiment analysis"""
    text: str
    sentiment: str  # Positive, Neutral, Negative
    score: float  # -1.0 to 1.0
    confidence: str  # low, medium, high


@router.post("/sentiment", response_model=SentimentResponse)
async def analyze_text_sentiment(request: SentimentRequest):
    """
    Phân tích cảm xúc của văn bản.
    
    - **text**: Văn bản cần phân tích (1-5000 ký tự)
    
    Returns:
    - **sentiment**: Positive / Neutral / Negative
    - **score**: Điểm số (-1.0 đến 1.0)
    - **confidence**: Độ tin cậy (low / medium / high)
    
    Model: cardiffnlp/twitter-roberta-base-sentiment (RoBERTa)
    """
    try:
        label, score = analyze_sentiment(request.text)
        
        # Determine confidence level
        abs_score = abs(score)
        if abs_score >= 0.8:
            confidence = "high"
        elif abs_score >= 0.5:
            confidence = "medium"
        else:
            confidence = "low"
        
        return SentimentResponse(
            text=request.text[:100] + "..." if len(request.text) > 100 else request.text,
            sentiment=label,
            score=round(score, 4),
            confidence=confidence
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")


class BatchSentimentRequest(BaseModel):
    """Request body for batch sentiment analysis"""
    texts: list[str] = Field(..., min_items=1, max_items=20, description="List of texts to analyze")


class BatchSentimentItem(BaseModel):
    """Single item in batch response"""
    text: str
    sentiment: str
    score: float


class BatchSentimentResponse(BaseModel):
    """Response from batch sentiment analysis"""
    results: list[BatchSentimentItem]
    summary: dict


@router.post("/sentiment/batch", response_model=BatchSentimentResponse)
async def analyze_batch_sentiment(request: BatchSentimentRequest):
    """
    Phân tích cảm xúc nhiều văn bản cùng lúc (tối đa 20).
    
    - **texts**: Danh sách văn bản cần phân tích
    
    Returns:
    - **results**: Kết quả phân tích từng văn bản
    - **summary**: Tổng hợp (positive_count, negative_count, neutral_count)
    """
    results = []
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    
    for text in request.texts:
        try:
            label, score = analyze_sentiment(text)
            results.append(BatchSentimentItem(
                text=text[:50] + "..." if len(text) > 50 else text,
                sentiment=label,
                score=round(score, 4)
            ))
            
            if label == "Positive":
                positive_count += 1
            elif label == "Negative":
                negative_count += 1
            else:
                neutral_count += 1
        except:
            results.append(BatchSentimentItem(
                text=text[:50] + "...",
                sentiment="Error",
                score=0.0
            ))
    
    return BatchSentimentResponse(
        results=results,
        summary={
            "total": len(request.texts),
            "positive": positive_count,
            "negative": negative_count,
            "neutral": neutral_count
        }
    )


# ============================================
# TOXIC CONTENT DETECTION
# Integrated with FastAPI (no external Flask API required)
# ============================================

from app.services.common.toxic_detection_service import get_toxic_detection_service, ToxicPrediction


class ToxicRequest(BaseModel):
    """Request body for toxic detection"""
    text: str = Field(..., min_length=1, max_length=10000, description="Text to analyze")
    threshold: Optional[float] = Field(0.5, ge=0.0, le=1.0, description="Classification threshold")


class ToxicResponse(BaseModel):
    """Response from toxic detection"""
    text: str
    is_violation: bool
    label: str  # VIOLATION or CLEAN
    confidence: float
    toxic_labels: list[str] = []
    predictions: dict = {}


@router.get("/toxic/health")
async def toxic_health_check():
    """
    Kiểm tra trạng thái của Toxic Detection Model.
    
    Model được tích hợp trực tiếp vào FastAPI.
    """
    service = get_toxic_detection_service()
    is_healthy = await service.check_health()
    
    return {
        "status": "healthy" if is_healthy else "models_not_loaded",
        "integrated": True,
        "models_path": str(service.models_path),
        "message": "Toxic detection model is ready" if is_healthy else "Models not loaded. Run: cd Only_Model && python save_models.py"
    }


@router.post("/toxic", response_model=ToxicResponse)
async def detect_toxic_content(request: ToxicRequest):
    """
    Phát hiện nội dung độc hại (toxic/violation).
    
    - **text**: Văn bản cần phân tích
    - **threshold**: Ngưỡng phân loại (mặc định 0.5)
    
    Returns:
    - **is_violation**: True nếu phát hiện nội dung vi phạm
    - **label**: VIOLATION hoặc CLEAN
    - **confidence**: Độ tin cậy (0-1)
    - **toxic_labels**: Các loại vi phạm (toxic, insult, threat, ...)
    
    Model: TF-IDF + Logistic Regression (integrated)
    """
    service = get_toxic_detection_service()
    
    # Check if models are loaded
    is_healthy = await service.check_health()
    if not is_healthy:
        raise HTTPException(
            status_code=503, 
            detail="Toxic detection models not loaded. Run: cd Only_Model && python save_models.py"
        )
    
    result = await service.analyze_text(request.text, request.threshold)
    
    return ToxicResponse(
        text=request.text[:100] + "..." if len(request.text) > 100 else request.text,
        is_violation=result.is_violation,
        label=result.label,
        confidence=result.confidence,
        toxic_labels=result.toxic_labels,
        predictions=result.predictions
    )


class BatchToxicRequest(BaseModel):
    """Request body for batch toxic detection"""
    texts: list[str] = Field(..., min_items=1, max_items=100, description="List of texts to analyze")
    threshold: Optional[float] = Field(0.5, ge=0.0, le=1.0, description="Classification threshold")


class BatchToxicItem(BaseModel):
    """Single item in batch response"""
    text: str
    is_violation: bool
    label: str
    confidence: float
    toxic_labels: list[str] = []


class BatchToxicResponse(BaseModel):
    """Response from batch toxic detection"""
    results: list[BatchToxicItem]
    summary: dict


@router.post("/toxic/batch", response_model=BatchToxicResponse)
async def detect_toxic_batch(request: BatchToxicRequest):
    """
    Phát hiện nội dung độc hại cho nhiều văn bản (tối đa 100).
    
    - **texts**: Danh sách văn bản cần phân tích
    - **threshold**: Ngưỡng phân loại
    
    Returns:
    - **results**: Kết quả phân tích từng văn bản
    - **summary**: Tổng hợp (total, toxic, clean, toxic_percentage)
    
    Model: TF-IDF + Logistic Regression (integrated)
    """
    service = get_toxic_detection_service()
    
    # Check if models are loaded
    is_healthy = await service.check_health()
    if not is_healthy:
        raise HTTPException(
            status_code=503, 
            detail="Toxic detection models not loaded. Run: cd Only_Model && python save_models.py"
        )
    
    data = await service.analyze_batch(request.texts, request.threshold)
    
    if "error" in data and data.get("error"):
        raise HTTPException(status_code=500, detail=data["error"])
    
    results = []
    for item in data.get("results", []):
        results.append(BatchToxicItem(
            text=item.get("text", "")[:50] + "..." if len(item.get("text", "")) > 50 else item.get("text", ""),
            is_violation=item.get("is_violation", False),
            label=item.get("label", "CLEAN"),
            confidence=item.get("confidence", 0.0),
            toxic_labels=item.get("toxic_labels", [])
        ))
    
    return BatchToxicResponse(
        results=results,
        summary=data.get("summary", {"total": len(request.texts), "toxic": 0, "clean": len(request.texts)})
    )

