from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import asyncio
import uuid
import os
from datetime import datetime

from database import SessionLocal
from models import (
    User, APIKey, Model, TestRun, CodeSession, 
    PromptTemplate, ModelBenchmark, CollaborationSession
)
from schemas import (
    APIKeyCreate, APIKeyResponse, ModelCreate, ModelResponse,
    LLMGenerateRequest, LLMGenerateResponse,
    CodeExecutionRequest, CodeExecutionResponse,
    CodeAnalysisRequest, CodeAnalysisResponse,
    AutoTestGenerationRequest, AutoTestGenerationResponse,
    CodeSessionCreate, CodeSessionResponse,
    PromptTemplateCreate, PromptTemplateResponse,
    ModelBenchmarkCreate, ModelBenchmarkResponse,
    ModelComparisonRequest, ModelComparisonResponse,
    CollaborationSessionCreate, CollaborationSessionResponse,
    CodeSuggestionResponse # Import new schema
)
from SKYNET.backend.skynet_providers import LLMProviderFactory, ModelProvider, ModelRegistry
from code_testing import (
    CodeAnalyzer, UnitTestGenerator, CodeExecutor, 
    CodeProfiler, IntegrityChecker
)
from websocket_manager import ConnectionManager
import base64
from cryptography.fernet import Fernet

# Create routers for different API sections
llm_router = APIRouter(tags=["LLM"])
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

# Auth dependency
from fastapi.security import HTTPBearer
from auth import verify_token

security = HTTPBearer()

async def get_current_user_dependency(
    token: str = Depends(security),
    db: Session = Depends(get_db)
):
    from fastapi import HTTPException
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token.credentials)
    if payload is None:
        raise credentials_exception
    
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    return user

# Encryption utilities for API keys
def get_encryption_key():
    """Get or generate encryption key for API keys"""
    import os
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        # Generate a new key if not exists
        key = Fernet.generate_key()
        # In production, store this key securely
    return key

def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key"""
    f = Fernet(get_encryption_key())
    return f.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key"""
    f = Fernet(get_encryption_key())
    return f.decrypt(encrypted_key.encode()).decode()

# ============= LLM API Routes =============

@llm_router.post("/api-keys", response_model=APIKeyResponse)
async def add_api_key(
    api_key_data: APIKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Add an API key for LLM providers"""
    # Encrypt the API key before storing
    encrypted_key = encrypt_api_key(api_key_data.api_key)
    
    api_key = APIKey(
        user_id=current_user.id,
        provider=api_key_data.provider,
        encrypted_key=encrypted_key,
        is_active=True
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    return APIKeyResponse(
        id=api_key.id,
        provider=api_key.provider,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        last_used=api_key.last_used,
        usage_count=api_key.usage_count
    )

@llm_router.get("/api-keys", response_model=List[APIKeyResponse])
async def get_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get user's API keys"""
    user_id = current_user.id
    api_keys = db.query(APIKey).filter(APIKey.user_id == user_id).all()
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

@llm_router.get("/chat-history", response_model=List[ChatHistoryResponse])
async def get_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get user's chat history"""
    user_id = current_user.id
    chat_sessions = db.query(ChatHistory).filter(ChatHistory.user_id == user_id).all()
    return [
        ChatHistoryResponse(
            id=session.id,
            user_id=session.user_id,
            session_id=session.session_id,
            model_id=session.model_id,
            model_name=session.model_name,
            messages=session.messages,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at
        ) for session in chat_sessions
    ]

@llm_router.delete("/chat-history/{session_id}")
async def delete_chat_history(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Delete a specific chat session from history"""
    user_id = current_user.id
    chat_session = db.query(ChatHistory).filter(
        ChatHistory.session_id == session_id,
        ChatHistory.user_id == user_id
    ).first()

    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    db.delete(chat_session)
    db.commit()
    return {"message": "Chat session deleted successfully"}


@llm_router.get("/available-models")
async def get_available_models():
    """Get list of available LLM models"""
    return ModelRegistry.get_available_models()

@llm_router.post("/generate", response_model=LLMGenerateResponse)
async def generate_llm_response(
    request: LLMGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Generate response from LLM model"""
    # Get the model
    model = db.query(Model).filter(Model.id == request.model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Get API key for the provider
    user_id = current_user.id
    api_key = db.query(APIKey).filter(
        APIKey.user_id == user_id,
        APIKey.provider == model.provider,
        APIKey.is_active == True
    ).first()
    
    if not api_key and model.provider != "custom":
        raise HTTPException(status_code=400, detail=f"No API key found for {model.provider}")
    
    try:
        # Create provider instance
        provider = LLMProviderFactory.create_provider(
            ModelProvider(model.provider),
            api_key.encrypted_key if api_key else None,
            model_path=model.file_path
        )
        
        # Generate response
        import time
        start_time = time.time()
        
        if request.stream:
            # For streaming, we'd return a different response type
            response = await provider.generate(
                request.prompt,
                model=model.model_identifier,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
        else:
            response = await provider.generate(
                request.prompt,
                model=model.model_identifier,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
        
        execution_time = time.time() - start_time
        
        # Update model statistics
        model.total_requests += 1
        model.avg_response_time = (
            (model.avg_response_time * (model.total_requests - 1) + execution_time) 
            / model.total_requests
        )
        if response["success"]:
            model.success_rate = ((model.success_rate * (model.total_requests - 1) + 100) 
                                 / model.total_requests)
        db.commit()
        
        # Update API key usage
        if api_key:
            api_key.usage_count += 1
            api_key.last_used = datetime.utcnow()
            db.commit()
        
        return LLMGenerateResponse(
            success=response["success"],
            response=response.get("response"),
            usage=response.get("usage"),
            model=response.get("model", model.name),
            error=response.get("error"),
            execution_time=execution_time
        )
        
    except Exception as e:
        return LLMGenerateResponse(
            success=False,
            response=None,
            usage=None,
            model=model.name,
            error=str(e),
            execution_time=0
        )

# ============= Code Testing API Routes =============

@code_router.post("/analyze", response_model=CodeAnalysisResponse)
async def analyze_code(request: CodeAnalysisRequest):
    """Analyze Python code for quality and issues"""
    analysis = CodeAnalyzer.analyze_code(request.code)
    
    if "error" in analysis:
        raise HTTPException(status_code=400, detail=analysis["error"])
    
    # Add integrity check
    integrity = IntegrityChecker.check_integrity(request.code)
    
    # Add performance profiling
    profile = await CodeProfiler.profile_code(request.code)
    
    return CodeAnalysisResponse(
        functions=analysis["functions"],
        classes=analysis["classes"],
        imports=analysis["imports"],
        variables=analysis.get("variables", []),
        complexity=analysis["complexity"],
        lines_of_code=analysis["lines_of_code"],
        issues=analysis["issues"],
        integrity_check=integrity,
        performance_metrics=profile
    )

@code_router.post("/generate-tests", response_model=AutoTestGenerationResponse)
async def generate_tests(request: AutoTestGenerationRequest):
    """Generate unit tests automatically for code"""
    # Analyze code first
    analysis = CodeAnalyzer.analyze_code(request.code)
    
    if "error" in analysis:
        raise HTTPException(status_code=400, detail=analysis["error"])
    
    # Generate tests
    test_code = UnitTestGenerator.generate_tests(request.code, analysis)
    
    # Count test methods
    test_count = test_code.count("def test_")
    
    # Estimate coverage (simplified)
    total_functions = len(analysis.get("functions", []))
    total_methods = sum(len(cls.get("methods", [])) for cls in analysis.get("classes", []))
    total_testable = total_functions + total_methods
    coverage_estimate = (test_count / max(total_testable, 1)) * 100 if total_testable > 0 else 0
    
    return AutoTestGenerationResponse(
        test_code=test_code,
        test_count=test_count,
        coverage_estimate=min(coverage_estimate, 100)
    )

@code_router.post("/execute", response_model=CodeExecutionResponse)
async def execute_code(request: CodeExecutionRequest):
    """Execute Python code safely with performance monitoring"""
    # Execute the code
    result = await CodeExecutor.execute_code(request.code)
    
    # Generate tests if requested
    test_results = []
    if request.generate_tests:
        analysis = CodeAnalyzer.analyze_code(request.code)
        if "error" not in analysis:
            test_code = UnitTestGenerator.generate_tests(request.code, analysis)
            test_results = await CodeExecutor.run_tests(test_code)
            test_results = [
                {
                    "test_name": t.test_name,
                    "passed": t.passed,
                    "error_message": t.error_message,
                    "execution_time": t.execution_time
                } for t in test_results
            ]
    
    return CodeExecutionResponse(
        success=result["success"],
        output=result["output"],
        error=result["error"],
        execution_time=result["execution_time"],
        memory_usage=result["memory_usage"],
        cpu_usage=result["cpu_usage"],
        test_results=test_results if test_results else None
    )

@code_router.post("/suggest", response_model=CodeSuggestionResponse)
async def get_code_suggestion(
    request: CodeAnalysisRequest, # Reusing CodeAnalysisRequest for simplicity
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Generate AI code suggestions or optimizations"""
    # For demonstration, we'll use a default model and API key.
    # In a real scenario, you'd allow the user to select a model
    # and ensure they have an active API key for it.
    
    # Find a suitable model (e.g., the first active OpenAI model)
    model = db.query(Model).filter(
        Model.provider == "openai",
        Model.type == "llm",
        Model.status == "active"
    ).first()

    if not model:
        raise HTTPException(status_code=404, detail="No active OpenAI model found for suggestions.")

    api_key_entry = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.provider == model.provider,
        APIKey.is_active == True
    ).first()

    if not api_key_entry:
        raise HTTPException(status_code=400, detail=f"No active API key found for {model.provider}. Please configure your API keys.")

    try:
        provider = LLMProviderFactory.create_provider(
            ModelProvider(model.provider),
            decrypt_api_key(api_key_entry.encrypted_key)
        )
        
        prompt = f"Given the following Python code, provide suggestions for optimization, best practices, or new features. Focus on improving the code quality and efficiency:\n\n```python\n{request.code}\n```\n\nProvide your suggestions in a concise markdown format, highlighting code changes where applicable."
        
        response = await provider.generate(
            prompt,
            model=model.model_identifier,
            temperature=0.7,
            max_tokens=1000
        )
        
        if response["success"]:
            return CodeSuggestionResponse(suggestion=response["response"])
        else:
            raise HTTPException(status_code=500, detail=f"AI suggestion failed: {response.get('error', 'Unknown error')}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get AI suggestion: {str(e)}")


@code_router.post("/sessions", response_model=CodeSessionResponse)
async def create_code_session(
    session_data: CodeSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Create a new code testing session"""
    user_id = current_user.id
    
    # Analyze the code
    analysis = CodeAnalyzer.analyze_code(session_data.code)
    profile = await CodeProfiler.profile_code(session_data.code)
    integrity = IntegrityChecker.check_integrity(session_data.code)
    
    # Generate tests
    test_code = ""
    if "error" not in analysis:
        test_code = UnitTestGenerator.generate_tests(session_data.code, analysis)
    
    # Create session
    session = CodeSession(
        user_id=user_id,
        name=session_data.name,
        code=session_data.code,
        language=session_data.language,
        test_code=test_code,
        analysis_result=analysis,
        performance_metrics=profile,
        integrity_check=integrity,
        auto_tests=test_code
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
async def get_code_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get user's code sessions"""
    user_id = current_user.id
    sessions = db.query(CodeSession).filter(CodeSession.user_id == user_id).all()
    
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

# ============= Model Management API Routes =============

@model_router.post("/", response_model=ModelResponse)
async def create_model(
    model_data: ModelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Create a new model configuration"""
    user_id = current_user.id
    
    model = Model(
        user_id=user_id,
        name=model_data.name,
        type=model_data.type,
        provider=model_data.provider,
        model_identifier=model_data.model_identifier,
        file_path=model_data.file_path,
        config=model_data.config,
        description=model_data.description,
        tags=model_data.tags,
        is_public=model_data.is_public,
        status="created"
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
        tags=model.tags,
        is_public=model.is_public,
        avg_response_time=model.avg_response_time,
        total_requests=model.total_requests,
        success_rate=model.success_rate
    )

@model_router.post("/upload")
async def upload_custom_model(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Upload a custom model file"""
    user_id = current_user.id
    
    # Create upload directory if it doesn't exist
    upload_dir = f"uploads/models/{user_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save the file
    file_path = f"{upload_dir}/{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create model entry
    model = Model(
        user_id=user_id,
        name=file.filename.split('.')[0],
        type="custom",
        provider="custom",
        file_path=file_path,
        status="uploaded"
    )
    
    db.add(model)
    db.commit()
    
    return {"message": "Model uploaded successfully", "model_id": model.id, "path": file_path}

@model_router.post("/compare", response_model=ModelComparisonResponse)
async def compare_models(
    request: ModelComparisonRequest,
    db: Session = Depends(get_db)
):
    """Compare multiple models with the same prompt"""
    results = []
    
    for model_id in request.model_ids:
        model = db.query(Model).filter(Model.id == model_id).first()
        if not model:
            continue
        
        # Get API key for the model's provider
        api_key = db.query(APIKey).filter(
            APIKey.provider == model.provider,
            APIKey.is_active == True
        ).first()
        
        if not api_key and model.provider != "custom":
            results.append({
                "model_id": model_id,
                "model_name": model.name,
                "error": f"No API key for {model.provider}"
            })
            continue
        
        try:
            provider = LLMProviderFactory.create_provider(
                ModelProvider(model.provider),
                api_key.encrypted_key if api_key else None,
                model_path=model.file_path
            )
            
            import time
            start_time = time.time()
            response = await provider.generate(request.test_prompt)
            execution_time = time.time() - start_time
            
            results.append({
                "model_id": model_id,
                "model_name": model.name,
                "response": response.get("response"),
                "execution_time": execution_time,
                "tokens_used": response.get("usage", {}).get("total_tokens", 0)
            })
        except Exception as e:
            results.append({
                "model_id": model_id,
                "model_name": model.name,
                "error": str(e)
            })
    
    # Determine winner based on execution time and success
    successful_results = [r for r in results if "error" not in r]
    winner = None
    if successful_results:
        winner = min(successful_results, key=lambda x: x["execution_time"])["model_id"]
    
    return ModelComparisonResponse(
        comparison_id=str(uuid.uuid4()),
        results=results,
        winner=winner,
        metrics={
            "total_models": len(request.model_ids),
            "successful": len(successful_results),
            "failed": len(results) - len(successful_results)
        }
    )

# ============= Collaboration API Routes =============

@collab_router.post("/sessions", response_model=CollaborationSessionResponse)
async def create_collaboration_session(
    session_data: CollaborationSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Create a new collaboration session"""
    user_id = current_user.id
    session_id = str(uuid.uuid4())
    
    session = CollaborationSession(
        name=session_data.name,
        description=session_data.description,
        created_by=user_id,
        session_id=session_id,
        is_active=True,
        participants=[user_id]
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

@collab_router.websocket("/ws/{session_id}")
async def collaboration_websocket(websocket: WebSocket, session_id: str, db: Session = Depends(get_db)):
    """WebSocket endpoint for real-time collaboration"""
    await manager.connect(websocket, session_id)
    
    # Get the collaboration session
    session = db.query(CollaborationSession).filter(
        CollaborationSession.session_id == session_id
    ).first()
    
    if not session:
        await websocket.close(code=4004)
        return
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message["type"] == "code_update":
                # Broadcast code changes to all participants
                await manager.broadcast_to_session(
                    session_id,
                    json.dumps({
                        "type": "code_update",
                        "data": message["data"],
                        "user": message.get("user")
                    })
                )
            
            elif message["type"] == "model_test":
                # Handle collaborative model testing
                await manager.broadcast_to_session(
                    session_id,
                    json.dumps({
                        "type": "model_test_result",
                        "data": message["data"],
                        "user": message.get("user")
                    })
                )
            
            elif message["type"] == "chat":
                # Update chat history in database
                if session.chat_history is None:
                    session.chat_history = []
                session.chat_history.append({
                    "user": message.get("user"),
                    "message": message["data"]["message"],
                    "timestamp": datetime.utcnow().isoformat()
                })
                db.commit()
                
                # Broadcast chat message
                await manager.broadcast_to_session(
                    session_id,
                    json.dumps({
                        "type": "chat",
                        "data": message["data"],
                        "user": message.get("user")
                    })
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        await manager.broadcast_to_session(
            session_id,
            json.dumps({
                "type": "user_disconnected",
                "data": {"message": "A user has left the session"}
            })
        )

# ============= Prompt Template API Routes =============

@model_router.post("/prompts", response_model=PromptTemplateResponse)
async def create_prompt_template(
    prompt_data: PromptTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Create a new prompt template"""
    user_id = current_user.id
    
    prompt = PromptTemplate(
        user_id=user_id,
        name=prompt_data.name,
        description=prompt_data.description,
        template=prompt_data.template,
        variables=prompt_data.variables,
        category=prompt_data.category,
        is_public=prompt_data.is_public
    )
    
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    
    return PromptTemplateResponse(
        id=prompt.id,
        user_id=prompt.user_id,
        name=prompt.name,
        description=prompt.description,
        template=prompt.template,
        variables=prompt.variables,
        category=prompt.category,
        is_public=prompt.is_public,
        usage_count=prompt.usage_count,
        rating=prompt.rating,
        created_at=prompt.created_at
    )

@model_router.get("/prompts", response_model=List[PromptTemplateResponse])
async def get_prompt_templates(
    category: str = None,
    public_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get prompt templates"""
    user_id = current_user.id
    
    query = db.query(PromptTemplate)
    
    if public_only:
        query = query.filter(PromptTemplate.is_public == True)
    else:
        query = query.filter(
            (PromptTemplate.user_id == user_id) | 
            (PromptTemplate.is_public == True)
        )
    
    if category:
        query = query.filter(PromptTemplate.category == category)
    
    prompts = query.all()
    
    return [
        PromptTemplateResponse(
            id=p.id,
            user_id=p.user_id,
            name=p.name,
            description=p.description,
            template=p.template,
            variables=p.variables,
            category=p.category,
            is_public=p.is_public,
            usage_count=p.usage_count,
            rating=p.rating,
            created_at=p.created_at
        ) for p in prompts
    ]
