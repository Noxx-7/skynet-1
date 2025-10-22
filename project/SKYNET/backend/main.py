from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import json
import logging
import os

from database import SessionLocal, engine, Base, get_db
from models import (
    User, Model, TestRun, CollaborationSession, APIKey, CodeSession,
    PromptTemplate, ModelBenchmark, ModelMarketplace, UsageStatistics, SystemMetrics
)
from schemas import (
    UserCreate, UserResponse, ModelCreate, ModelResponse,
    TestRunCreate, TestRunResponse, CodeExecutionRequest,
    CodeExecutionResponse
)
from websocket_manager import ConnectionManager

# Import the simplified no-auth API routers
from api_routes_no_auth import skynet_router, code_router, model_router, collab_router, market_router, chat_history_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Skynet Playground API", version="2.0.0", description="Complete Skynet IDE Platform - No Auth")

# Allow all origins for demo purposes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()

# Include all the simplified routers
app.include_router(skynet_router, prefix="/llm", tags=["Skynet"])
app.include_router(code_router, prefix="/code", tags=["Code Testing"])
app.include_router(model_router, prefix="/models", tags=["Models"])
app.include_router(collab_router, prefix="/collaboration", tags=["Collaboration"])
app.include_router(market_router, prefix="/marketplace", tags=["Marketplace"])
app.include_router(chat_history_router, prefix="/api", tags=["Chat History"])

# Legacy endpoint for backward compatibility with frontend
@app.get("/models", response_model=list[ModelResponse])
async def get_models_legacy(db: Session = Depends(get_db)):
    # Use guest user models
    models = db.query(Model).filter((Model.user_id == "guest-user") | (Model.is_public == True)).all()
    return [
        ModelResponse(
            id=model.id,
            name=model.name,
            type=model.type,
            status=model.status,
            user_id=model.user_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            file_path=model.file_path,
            config=model.config,
            provider=model.provider,
            model_identifier=model.model_identifier,
            description=model.description,
            tags=model.tags if model.tags else [],
            is_public=model.is_public,
            avg_response_time=model.avg_response_time,
            total_requests=model.total_requests,
            success_rate=model.success_rate
        ) for model in models
    ]

@app.post("/execute")
async def execute_code(execution_request: CodeExecutionRequest):
    # Import code testing module
    from code_testing import CodeExecutor
    
    # Execute the code
    result = await CodeExecutor.execute_code(execution_request.code)
    
    return CodeExecutionResponse(
        success=result["success"],
        output=result["output"],
        error=result["error"],
        execution_time=result["execution_time"],
        memory_usage=result["memory_usage"],
        cpu_usage=result["cpu_usage"],
        test_results=result.get("test_results")
    )

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
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
                    "user": message.get("user", "guest")
                })
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)

@app.get("/")
async def root():
    return {
        "message": "Skynet Playground API v2.0 - No Authentication Required", 
        "status": "running",
        "features": [
            "Multi-Model Support (OpenAI, Anthropic, Gemini)",
            "Custom Model Upload",
            "Auto Unit Test Generation",
            "Code Performance Profiling",
            "Model Benchmarking",
            "Real-time Collaboration",
            "Prompt Template Library",
            "Model Marketplace"
        ],
        "note": "All features accessible without login"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "auth_required": False,
        "services": {
            "database": "connected",
            "skynet_providers": ["openai", "anthropic", "gemini", "custom"],
            "features": {
                "code_testing": "enabled",
                "model_upload": "enabled",
                "collaboration": "enabled",
                "marketplace": "enabled"
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)