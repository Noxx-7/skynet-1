# Simplified API Routes without Authentication
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any, Optional
import asyncio
import json
import uuid
import os
from cryptography.fernet import Fernet

from database import SessionLocal
from supabase_client import get_supabase_client
from models import (
    User, Model, TestRun, CollaborationSession, APIKey,
    CodeSession, PromptTemplate, ModelBenchmark,
    UsageStatistics, ChatHistory
)
from schemas import (
    APIKeyCreate, APIKeyResponse, ModelCreate, ModelResponse,
    SkynetGenerateRequest, SkynetGenerateResponse,
    CodeExecutionRequest, CodeExecutionResponse,
    CodeAnalysisRequest, CodeAnalysisResponse,
    AutoTestGenerationRequest, AutoTestGenerationResponse,
    CodeSessionCreate, CodeSessionResponse,
    PromptTemplateCreate, PromptTemplateResponse,
    ModelBenchmarkCreate, ModelBenchmarkResponse,
    ModelComparisonRequest, ModelComparisonResponse,
    CollaborationSessionCreate, CollaborationSessionResponse,
    ChatHistoryCreate, ChatHistoryUpdate, ChatHistoryResponse,
    CodeOptimizationRequest, CodeOptimizationResponse
)
from skynet_providers import SkynetProviderFactory, ModelProvider, ModelRegistry
from code_testing import (
    CodeAnalyzer, UnitTestGenerator, CodeExecutor, 
    CodeProfiler, IntegrityChecker
)
from websocket_manager import ConnectionManager

# Create routers for different API sections
skynet_router = APIRouter(tags=["Skynet"])
code_router = APIRouter(tags=["Code Testing"])
model_router = APIRouter(tags=["Models"])
collab_router = APIRouter(tags=["Collaboration"])
market_router = APIRouter(tags=["Marketplace"])

# WebSocket manager
manager = ConnectionManager()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create a default user ID for non-authenticated sessions
DEFAULT_USER_ID = "guest-user"

# Encryption utilities for API keys
def get_encryption_key():
    """Get encryption key for API keys - must be set in environment"""
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        # CRITICAL: ENCRYPTION_KEY must be set for persistence
        # If not set, try JWT_SECRET_KEY as fallback
        jwt_key = os.getenv("JWT_SECRET_KEY")
        if jwt_key:
            # Use JWT_SECRET_KEY as base for Fernet key (must be 32 url-safe base64-encoded bytes)
            import base64
            import hashlib
            # Hash JWT_SECRET_KEY to get consistent 32 bytes
            hashed = hashlib.sha256(jwt_key.encode()).digest()
            key = base64.urlsafe_b64encode(hashed)
        else:
            raise ValueError("ENCRYPTION_KEY or JWT_SECRET_KEY must be set in environment for API key encryption")
    return key

def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key"""
    f = Fernet(get_encryption_key())
    return f.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key"""
    f = Fernet(get_encryption_key())
    return f.decrypt(encrypted_key.encode()).decode()

# Create cipher suite for quick decryption
cipher_suite = Fernet(get_encryption_key())

# Helper function to auto-register models when API key is added
async def auto_register_provider_models(provider: str, db: Session):
    """Automatically register models for a provider when API key is added"""
    available_models = ModelRegistry.get_available_models()

    if provider not in available_models:
        return

    for model_info in available_models[provider]:
        model_id = model_info["id"]
        model_name = model_info["name"]

        # Check if model already exists
        existing_model = db.query(Model).filter(
            Model.user_id == DEFAULT_USER_ID,
            Model.provider == provider,
            Model.model_identifier == model_id
        ).first()

        if not existing_model:
            # Create new model entry
            new_model = Model(
                name=model_name,
                type="api",
                user_id=DEFAULT_USER_ID,
                provider=provider,
                model_identifier=model_id,
                status="active",
                is_public=False,
                description=f"{model_name} from {provider}",
                config={"context_length": model_info.get("context", 0), "vision": model_info.get("vision", False)}
            )
            db.add(new_model)

    db.commit()

# ============= Skynet API Routes =============

@skynet_router.post("/api-keys", response_model=APIKeyResponse)
async def add_api_key(
    api_key_data: APIKeyCreate,
    db: Session = Depends(get_db)
):

    """Add an API key for LLM providers - No auth required"""
    # Encrypt the API key before storing
    encrypted_key = encrypt_api_key(api_key_data.api_key)

    # Check if API key already exists for this provider
    existing_key = db.query(APIKey).filter(
        APIKey.user_id == DEFAULT_USER_ID,
        APIKey.provider == api_key_data.provider
    ).first()

    if existing_key:
        # Update existing key
        existing_key.encrypted_key = encrypted_key
        existing_key.is_active = True
        db.commit()
        db.refresh(existing_key)
        api_key = existing_key
    else:
        # Create new key
        api_key = APIKey(
            user_id=DEFAULT_USER_ID,
            provider=api_key_data.provider,
            encrypted_key=encrypted_key,
            is_active=True
        )
        db.add(api_key)
        db.commit()
        db.refresh(api_key)

    # Auto-register models for this provider
    await auto_register_provider_models(api_key_data.provider, db)

    return APIKeyResponse(
        id=api_key.id,
        provider=api_key.provider,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        last_used=api_key.last_used,
        usage_count=api_key.usage_count
    )

@skynet_router.get("/api-keys", response_model=List[APIKeyResponse])
async def get_api_keys(db: Session = Depends(get_db)):
    """Get API keys - No auth required"""
    api_keys = db.query(APIKey).filter(APIKey.user_id == DEFAULT_USER_ID).all()
    return [
        APIKeyResponse(
            id=key.id,
            provider=key.provider,
            is_active=key.is_active,
            created_at=key.created_at,
            last_used=key.last_used,
            usage_count=key.usage_count
        ) for key in api_keys
    ]

@skynet_router.get("/available-models")
async def get_available_models():
    """Get list of available LLM models"""
    return ModelRegistry.get_available_models()

@skynet_router.post("/check-model-health")
async def check_model_health(
    request: Dict[str, str],
    db: Session = Depends(get_db)
):
    """Check if a specific model is available and working"""
    provider_name = request.get("provider")
    model_id = request.get("model_id")

    if not provider_name or not model_id:
        raise HTTPException(status_code=400, detail="Provider and model_id are required")

    api_key_obj = db.query(APIKey).filter(
        APIKey.user_id == DEFAULT_USER_ID,
        APIKey.provider == provider_name,
        APIKey.is_active == True
    ).first()

    if not api_key_obj:
        return {
            "success": False,
            "available": False,
            "error": f"API key not configured for {provider_name}"
        }

    try:
        provider_enum_map = {
            "openai": ModelProvider.OPENAI,
            "anthropic": ModelProvider.ANTHROPIC,
            "gemini": ModelProvider.GEMINI
        }
        provider_enum = provider_enum_map.get(provider_name)

        if not provider_enum:
            return {
                "success": False,
                "available": False,
                "error": f"Unsupported provider: {provider_name}"
            }

        decrypted_key = cipher_suite.decrypt(api_key_obj.encrypted_key.encode()).decode()
        provider = SkynetProviderFactory.create_provider(provider_enum, decrypted_key)

        result = await provider.health_check(model_id)
        return result

    except Exception as e:
        return {
            "success": False,
            "available": False,
            "error": str(e)
        }

@skynet_router.post("/generate", response_model=SkynetGenerateResponse)
async def generate_skynet_response(
    request: SkynetGenerateRequest,
    db: Session = Depends(get_db)
):
    """Generate response from LLM model - No auth required"""
    # Get the model
    model = db.query(Model).filter(Model.id == request.model_id).first()
    
    # Determine provider from model ID or model object
    provider_name = None
    model_identifier = None
    
    if model:
        provider_name = model.provider
        model_identifier = model.model_identifier
    elif "-" in request.model_id:
        # Fallback for API models without DB records (e.g., "openai-gpt-4")
        provider_name = request.model_id.split("-")[0]
        model_identifier = request.model_id.replace(f"{provider_name}-", "")
    
    if provider_name in ["openai", "anthropic", "gemini"]:
        # Try to use a provider directly
        api_key_obj = db.query(APIKey).filter(
            APIKey.user_id == DEFAULT_USER_ID,
            APIKey.provider == provider_name,
            APIKey.is_active == True
        ).first()
        
        if api_key_obj:
            try:
                # Map provider name to ModelProvider enum
                provider_enum_map = {
                    "openai": ModelProvider.OPENAI,
                    "anthropic": ModelProvider.ANTHROPIC,
                    "gemini": ModelProvider.GEMINI
                }
                provider_enum = provider_enum_map.get(provider_name)
                
                # Decrypt the API key
                decrypted_key = cipher_suite.decrypt(api_key_obj.encrypted_key.encode()).decode()
                
                # Create provider instance
                provider = SkynetProviderFactory.create_provider(provider_enum, decrypted_key)
                response = await provider.generate(
                    prompt=request.prompt,
                    model=model_identifier,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                )

                # Check if the provider returned an error
                if not response.get("success", True):
                    return SkynetGenerateResponse(
                        success=False,
                        response=None,
                        usage=None,
                        model=request.model_id,
                        error=response.get("error", "Unknown error from provider"),
                        execution_time=0.0
                    )

                return SkynetGenerateResponse(
                    success=True,
                    response=response.get("response", ""),
                    usage=response.get("usage"),
                    model=request.model_id,
                    error=None,
                    execution_time=0.0
                )
            except Exception as e:
                return SkynetGenerateResponse(
                    success=False,
                    response=None,
                    usage=None,
                    model=request.model_id,
                    error=f"Error calling {provider_name}: {str(e)}",
                    execution_time=0.0
                )
        else:
            return SkynetGenerateResponse(
                success=False,
                response=None,
                usage=None,
                model=request.model_id,
                error=f"Please configure API key for {provider_name}",
                execution_time=0.0
            )
    
    # If custom model, use the model's handler
    if model and model.type == "custom":
        # Handle custom model execution
        response = await execute_custom_model(model, request.prompt)
        return SkynetGenerateResponse(
            success=True,
            response=response,
            usage=None,  # Add usage field
            model=model.name,
            error=None,
            execution_time=0.0
        )
    
    return SkynetGenerateResponse(
        success=False,
        response=None,
        usage=None,  # Add usage field
        model=request.model_id,
        error="Model not found or API key not configured",
        execution_time=0.0
    )

async def execute_custom_model(model: Model, prompt: str) -> str:
    """Execute a custom uploaded model"""
    # Simulated custom model execution
    return f"Response from custom model '{model.name}': {prompt[:50]}..."

# ============= Code Testing API Routes =============

@code_router.post("/execute", response_model=CodeExecutionResponse)
async def execute_code(
    request: CodeExecutionRequest,
    db: Session = Depends(get_db)
):
    """Execute Python code - No auth required"""
    result = await CodeExecutor.execute_code(request.code)
    return CodeExecutionResponse(
        success=result["success"],
        output=result["output"],
        error=result["error"],
        execution_time=result["execution_time"],
        memory_usage=result["memory_usage"],
        cpu_usage=result["cpu_usage"],
        test_results=result.get("test_results")
    )

@code_router.post("/analyze", response_model=CodeAnalysisResponse)
async def analyze_code(
    request: CodeAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze code complexity and quality - No auth required"""
    analysis = CodeAnalyzer.analyze_code(request.code)
    return CodeAnalysisResponse(
        complexity_score=analysis.get("complexity", 0),
        lines_of_code=analysis["lines_of_code"],
        functions=analysis["functions"],
        classes=analysis["classes"],
        issues=analysis.get("issues", []),
        suggestions=analysis.get("suggestions", [])
    )

@code_router.post("/generate-tests", response_model=AutoTestGenerationResponse)
async def generate_tests(
    request: AutoTestGenerationRequest,
    db: Session = Depends(get_db)
):
    """Generate unit tests automatically with difficulty selection - No auth required"""
    # First analyze the code to get structure
    analysis = CodeAnalyzer.analyze_code(request.code)
    
    # Enforce difficulty-based num_tests mapping (server-side validation)
    difficulty_map = {
        'low': 5,
        'mid': 15,
        'high': 25
    }
    num_tests = difficulty_map.get(request.difficulty, 15)
    
    # Generate tests based on analysis
    test_code = UnitTestGenerator.generate_tests(
        request.code,
        analysis,
        num_tests=num_tests
    )
    
    # Count tests
    test_count = test_code.count("def test_")
    
    return AutoTestGenerationResponse(
        test_code=test_code,
        test_count=test_count,
        coverage_estimate=min(test_count * 10, 95)
    )

@code_router.post("/profile")
async def profile_code(
    request: CodeExecutionRequest,
    db: Session = Depends(get_db)
):
    """Profile code performance - No auth required"""
    profile_data = await CodeProfiler.profile_code(request.code)
    return {
        "profile_data": profile_data,
        "success": True
    }

@code_router.post("/run-tests")
async def run_tests(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Run unit tests - No auth required"""
    original_code = request.get("code", "")
    test_code = request.get("test_code", "")

    combined_code = f"{original_code}\n\n{test_code}"

    test_results = await CodeExecutor.run_tests(combined_code)
    return {
        "test_results": test_results,
        "success": True,
        "output": "Tests executed"
    }

@code_router.post("/run-auto-tests")
async def run_auto_tests(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Generate and run tests automatically - No auth required"""
    code = request.get("code", "")
    difficulty = request.get("difficulty", "mid")

    analysis = CodeAnalyzer.analyze_code(code)

    difficulty_map = {
        'low': 5,
        'mid': 15,
        'high': 25
    }
    num_tests = difficulty_map.get(difficulty, 15)

    test_code = UnitTestGenerator.generate_tests(
        code,
        analysis,
        num_tests=num_tests
    )

    combined_code = f"{code}\n\n{test_code}"

    test_results = await CodeExecutor.run_tests(combined_code)

    return {
        "test_code": test_code,
        "test_results": test_results,
        "test_count": test_code.count("def test_"),
        "passed": sum(1 for t in test_results if t.get("passed", False)),
        "failed": sum(1 for t in test_results if not t.get("passed", True)),
        "success": True
    }

# ============= Code Session Routes =============

@code_router.post("/sessions", response_model=CodeSessionResponse)
async def create_code_session(
    session_data: CodeSessionCreate,
    db: Session = Depends(get_db)
):
    """Create a new code session - No auth required"""
    session = CodeSession(
        user_id=DEFAULT_USER_ID,
        name=session_data.name,
        code=session_data.code,
        language=session_data.language
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return CodeSessionResponse(
        id=session.id,
        user_id=session.user_id,
        name=session.name,
        code=session.code,
        language=session.language,
        test_code=session.test_code,
        analysis_result=session.analysis_result,
        performance_metrics=session.performance_metrics,
        integrity_check=session.integrity_check,
        auto_tests=session.auto_tests,
        created_at=session.created_at,
        updated_at=session.updated_at
    )

@code_router.get("/sessions", response_model=List[CodeSessionResponse])
async def get_code_sessions(db: Session = Depends(get_db)):
    """Get all code sessions - No auth required"""
    sessions = db.query(CodeSession).filter(
        CodeSession.user_id == DEFAULT_USER_ID
    ).order_by(CodeSession.created_at.desc()).limit(10).all()
    
    return [
        CodeSessionResponse(
            id=s.id,
            user_id=s.user_id,
            name=s.name,
            code=s.code,
            language=s.language,
            test_code=s.test_code,
            analysis_result=s.analysis_result,
            performance_metrics=s.performance_metrics,
            integrity_check=s.integrity_check,
            auto_tests=s.auto_tests,
            created_at=s.created_at,
            updated_at=s.updated_at
        ) for s in sessions
    ]

# ============= Model Management Routes =============

@model_router.post("/upload", response_model=ModelResponse)
async def upload_model(
    model_data: ModelCreate,
    db: Session = Depends(get_db)
):
    """Upload a custom model - No auth required"""
    model = Model(
        name=model_data.name,
        type=model_data.type,
        user_id=DEFAULT_USER_ID,
        provider=model_data.provider,
        model_identifier=model_data.model_identifier,
        file_path=model_data.file_path,
        config=model_data.config,
        description=model_data.description,
        tags=model_data.tags,
        is_public=model_data.is_public,
        status="uploaded"
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    
    return ModelResponse(
        id=model.id,
        name=model.name,
        type=model.type,
        status=model.status,
        user_id=model.user_id,
        provider=model.provider,
        model_identifier=model.model_identifier,
        created_at=model.created_at,
        updated_at=model.updated_at,
        file_path=model.file_path,
        config=model.config,
        description=model.description,
        tags=model.tags if model.tags else [],
        is_public=model.is_public,
        avg_response_time=model.avg_response_time,
        total_requests=model.total_requests,
        success_rate=model.success_rate
    )

@model_router.get("/list", response_model=List[ModelResponse])
async def list_models(db: Session = Depends(get_db)):
    """List all models - No auth required"""
    models = db.query(Model).filter(
        (Model.user_id == DEFAULT_USER_ID) | (Model.is_public == True)
    ).all()
    
    return [
        ModelResponse(
            id=m.id,
            name=m.name,
            type=m.type,
            status=m.status,
            user_id=m.user_id,
            provider=m.provider,
            model_identifier=m.model_identifier,
            created_at=m.created_at,
            updated_at=m.updated_at,
            file_path=m.file_path,
            config=m.config,
            description=m.description,
            tags=m.tags if m.tags else [],
            is_public=m.is_public,
            avg_response_time=m.avg_response_time,
            total_requests=m.total_requests,
            success_rate=m.success_rate
        ) for m in models
    ]

# ============= Collaboration Routes =============

@collab_router.post("/create", response_model=CollaborationSessionResponse)
async def create_collaboration_session(
    session_data: CollaborationSessionCreate,
    db: Session = Depends(get_db)
):
    """Create a collaboration session - No auth required"""
    session = CollaborationSession(
        name=session_data.name,
        session_id=str(uuid.uuid4()),
        created_by=DEFAULT_USER_ID,
        description=session_data.description,
        is_active=True,
        participants=[DEFAULT_USER_ID],
        shared_models=[]
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return CollaborationSessionResponse(
        id=session.id,
        name=session.name,
        session_id=session.session_id,
        created_by=session.created_by,
        description=session.description,
        is_active=session.is_active,
        participants=session.participants,
        shared_models=session.shared_models,
        created_at=session.created_at,
        updated_at=session.updated_at
    )

@collab_router.get("/sessions", response_model=List[CollaborationSessionResponse])
async def get_collaboration_sessions(db: Session = Depends(get_db)):
    """Get active collaboration sessions - No auth required"""
    sessions = db.query(CollaborationSession).filter(
        CollaborationSession.is_active == True
    ).limit(10).all()
    
    return [
        CollaborationSessionResponse(
            id=s.id,
            name=s.name,
            session_id=s.session_id,
            created_by=s.created_by,
            description=s.description,
            is_active=s.is_active,
            participants=s.participants if s.participants else [],
            shared_models=s.shared_models if s.shared_models else [],
            created_at=s.created_at,
            updated_at=s.updated_at
        ) for s in sessions
    ]

# WebSocket for real-time collaboration
@collab_router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str
):
    """WebSocket endpoint for collaboration - No auth required"""
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            await manager.broadcast_to_session(
                session_id,
                json.dumps({
                    "type": message["type"],
                    "data": message["data"],
                    "user": "guest"
                })
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)

# ============= Chat History Routes =============

chat_history_router = APIRouter(tags=["Chat History"])

@chat_history_router.post("/chat-history", response_model=ChatHistoryResponse)
async def create_chat_history(
    chat_data: ChatHistoryCreate,
    db: Session = Depends(get_db)
):
    """Create or update chat history using Supabase - No auth required"""
    try:
        supabase = get_supabase_client()

        # Check if chat already exists
        existing = supabase.table("chat_history").select("*").eq("session_id", chat_data.session_id).eq("user_id", DEFAULT_USER_ID).maybeSingle().execute()

        chat_data_dict = {
            "user_id": DEFAULT_USER_ID,
            "session_id": chat_data.session_id,
            "model_id": chat_data.model_id,
            "model_name": chat_data.model_name,
            "messages": chat_data.messages,
            "title": chat_data.title or f"Chat with {chat_data.model_name}",
            "updated_at": datetime.utcnow().isoformat()
        }

        if existing.data:
            # Update existing chat
            result = supabase.table("chat_history").update(chat_data_dict).eq("session_id", chat_data.session_id).eq("user_id", DEFAULT_USER_ID).execute()
            chat = result.data[0]
        else:
            # Create new chat
            result = supabase.table("chat_history").insert(chat_data_dict).execute()
            chat = result.data[0]

        return ChatHistoryResponse(
            id=chat["id"],
            user_id=chat["user_id"],
            session_id=chat["session_id"],
            model_id=chat.get("model_id"),
            model_name=chat["model_name"],
            messages=chat["messages"],
            title=chat.get("title"),
            created_at=datetime.fromisoformat(chat["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(chat["updated_at"].replace("Z", "+00:00")) if chat.get("updated_at") else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving chat history: {str(e)}")

@chat_history_router.get("/chat-history", response_model=List[ChatHistoryResponse])
async def get_chat_history(db: Session = Depends(get_db)):
    """Get all chat history using Supabase - No auth required"""
    try:
        supabase = get_supabase_client()
        result = supabase.table("chat_history").select("*").eq("user_id", DEFAULT_USER_ID).order("updated_at", desc=True).limit(50).execute()

        return [
            ChatHistoryResponse(
                id=chat["id"],
                user_id=chat["user_id"],
                session_id=chat["session_id"],
                model_id=chat.get("model_id"),
                model_name=chat["model_name"],
                messages=chat["messages"],
                title=chat.get("title"),
                created_at=datetime.fromisoformat(chat["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(chat["updated_at"].replace("Z", "+00:00")) if chat.get("updated_at") else None
            ) for chat in result.data
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat history: {str(e)}")

@chat_history_router.get("/chat-history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_by_session(session_id: str, db: Session = Depends(get_db)):
    """Get chat history by session ID using Supabase - No auth required"""
    try:
        supabase = get_supabase_client()
        result = supabase.table("chat_history").select("*").eq("session_id", session_id).eq("user_id", DEFAULT_USER_ID).maybeSingle().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Chat history not found")

        chat = result.data
        return ChatHistoryResponse(
            id=chat["id"],
            user_id=chat["user_id"],
            session_id=chat["session_id"],
            model_id=chat.get("model_id"),
            model_name=chat["model_name"],
            messages=chat["messages"],
            title=chat.get("title"),
            created_at=datetime.fromisoformat(chat["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(chat["updated_at"].replace("Z", "+00:00")) if chat.get("updated_at") else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat history: {str(e)}")

@chat_history_router.delete("/chat-history/{session_id}")
async def delete_chat_history(session_id: str, db: Session = Depends(get_db)):
    """Delete chat history by session ID using Supabase - No auth required"""
    try:
        supabase = get_supabase_client()
        result = supabase.table("chat_history").delete().eq("session_id", session_id).eq("user_id", DEFAULT_USER_ID).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Chat history not found")

        return {"success": True, "message": "Chat history deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting chat history: {str(e)}")

# ============= Code Optimization Routes =============

@code_router.post("/optimize", response_model=CodeOptimizationResponse)
async def optimize_code(
    request: CodeOptimizationRequest,
    db: Session = Depends(get_db)
):
    """Analyze code and provide optimization suggestions - No auth required"""
    analysis = CodeAnalyzer.analyze_code(request.code)

    improvements = []

    if analysis.get("complexity", 0) > 10:
        improvements.append({
            "type": "complexity",
            "severity": "high",
            "message": "Code complexity is high. Consider breaking down functions into smaller units.",
            "line": None
        })

    if len(analysis.get("issues", [])) > 0:
        for issue in analysis["issues"]:
            improvements.append({
                "type": "code_quality",
                "severity": "medium",
                "message": issue,
                "line": None
            })

    for suggestion in analysis.get("suggestions", []):
        improvements.append({
            "type": "optimization",
            "severity": "low",
            "message": suggestion,
            "line": None
        })

    optimized_code = request.code

    return CodeOptimizationResponse(
        original_code=request.code,
        optimized_code=optimized_code,
        improvements=improvements,
        performance_gain=None
    )

@code_router.post("/generate-optimized")
async def generate_optimized_code(
    request: CodeOptimizationRequest,
    db: Session = Depends(get_db)
):
    """Generate fully optimized code using LLM - No auth required"""
    api_key_obj = db.query(APIKey).filter(
        APIKey.user_id == DEFAULT_USER_ID,
        APIKey.is_active == True
    ).first()

    if not api_key_obj:
        raise HTTPException(status_code=400, detail="Please configure an API key first")

    try:
        provider_enum = ModelProvider.OPENAI
        if api_key_obj.provider == "anthropic":
            provider_enum = ModelProvider.ANTHROPIC
        elif api_key_obj.provider == "gemini":
            provider_enum = ModelProvider.GEMINI

        decrypted_key = cipher_suite.decrypt(api_key_obj.encrypted_key.encode()).decode()

        provider = SkynetProviderFactory.create_provider(provider_enum, decrypted_key)

        optimization_prompt = f"""Analyze and optimize the following {request.language} code. Provide:
1. Improved version with better performance and readability
2. Explanation of optimizations made

Code:
```{request.language}
{request.code}
```

Return the optimized code wrapped in ```{request.language} blocks."""

        response = await provider.generate(
            prompt=optimization_prompt,
            temperature=0.3,
            max_tokens=2000
        )

        if not response.get("success", True):
            raise HTTPException(status_code=500, detail=response.get("error", "Failed to generate optimized code"))

        optimized_text = response.get("response", "")

        return {
            "success": True,
            "original_code": request.code,
            "optimized_code": optimized_text,
            "provider": api_key_obj.provider
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating optimized code: {str(e)}")