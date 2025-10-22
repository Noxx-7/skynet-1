from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import re

# User schemas
class UserBase(BaseModel):
    email: str
    username: str

    @validator('email')
    def email_must_be_valid(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v

    class Config:
        protected_namespaces = ()

class UserCreate(UserBase):
    password: str

    @validator('password')
    def password_must_be_strong(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserResponse(UserBase):
    id: str
    created_at: datetime
    is_active: bool
    role: str
    preferences: Dict[str, Any]
    usage_limits: Dict[str, Any]

    class Config:
        from_attributes = True

# API Key schemas
class APIKeyCreate(BaseModel):
    provider: str
    api_key: str

class APIKeyResponse(BaseModel):
    id: str
    provider: str
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime]
    usage_count: int

    class Config:
        from_attributes = True

# Model schemas
class ModelBase(BaseModel):
    name: str
    type: str

    class Config:
        protected_namespaces = ()

class ModelCreate(ModelBase):
    provider: Optional[str] = None
    model_identifier: Optional[str] = None
    file_path: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    is_public: bool = False

class ModelResponse(ModelBase):
    id: str
    status: str
    user_id: str
    provider: Optional[str]
    model_identifier: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    file_path: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    description: Optional[str]
    tags: List[str]
    is_public: bool
    avg_response_time: float
    total_requests: int
    success_rate: float

    class Config:
        from_attributes = True

# Skynet Generation schemas
class SkynetGenerateRequest(BaseModel):
    prompt: str
    model_id: str
    temperature: float = 0.7
    max_tokens: int = 1000
    stream: bool = False
    parameters: Optional[Dict[str, Any]] = {}

class SkynetGenerateResponse(BaseModel):
    success: bool
    response: Optional[str]
    usage: Optional[Dict[str, Any]]
    model: str
    error: Optional[str]
    execution_time: float

# Test run schemas
class TestRunBase(BaseModel):
    name: str

class TestRunCreate(TestRunBase):
    model_id: str
    code: Optional[str]
    prompt: Optional[str]
    test_type: str = "unit_test"

class TestRunResponse(TestRunBase):
    id: str
    model_id: str
    user_id: str
    status: str
    results: Optional[Dict[str, Any]] = None
    execution_time: Optional[float]
    test_type: str
    metrics: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True

# Code execution schemas
class CodeExecutionRequest(BaseModel):
    code: str
    language: str = "python"
    model_id: Optional[str] = None
    generate_tests: bool = False
    analyze: bool = True
    profile: bool = False

class CodeExecutionResponse(BaseModel):
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: float
    memory_usage: float
    cpu_usage: float
    test_results: Optional[List[Dict[str, Any]]]

class CodeAnalysisRequest(BaseModel):
    code: str
    language: str = "python"

class CodeAnalysisResponse(BaseModel):
    functions: List[Dict[str, Any]]
    classes: List[Dict[str, Any]]
    imports: List[str]
    variables: List[str]
    complexity: int
    lines_of_code: int
    issues: List[str]
    integrity_check: Dict[str, Any]
    performance_metrics: Dict[str, Any]

class AutoTestGenerationRequest(BaseModel):
    code: str
    language: str = "python"
    test_type: str = "unit"  # unit, integration, performance
    difficulty: str = "mid"  # low, mid, high
    num_tests: int = 15  # 5 for low, 15 for mid, 25 for high

class AutoTestGenerationResponse(BaseModel):
    test_code: str
    test_count: int
    coverage_estimate: float

# Code session schemas
class CodeSessionCreate(BaseModel):
    name: str
    code: str
    language: str = "python"

class CodeSessionResponse(BaseModel):
    id: str
    user_id: str
    name: str
    code: str
    language: str
    test_code: Optional[str]
    analysis_result: Optional[Dict[str, Any]]
    performance_metrics: Optional[Dict[str, Any]]
    integrity_check: Optional[Dict[str, Any]]
    auto_tests: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Prompt template schemas
class PromptTemplateCreate(BaseModel):
    name: str
    description: Optional[str]
    template: str
    variables: List[str]
    category: str
    is_public: bool = False

class PromptTemplateResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    template: str
    variables: List[str]
    category: str
    is_public: bool
    usage_count: int
    rating: float
    created_at: datetime

    class Config:
        from_attributes = True

# Model benchmark schemas
class ModelBenchmarkCreate(BaseModel):
    model_id: str
    benchmark_name: str
    test_data: Optional[Dict[str, Any]]

class ModelBenchmarkResponse(BaseModel):
    id: str
    model_id: str
    benchmark_name: str
    score: float
    metrics: Dict[str, Any]
    test_data: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True

# Model marketplace schemas
class ModelMarketplaceResponse(BaseModel):
    id: str
    model_id: str
    price: float
    downloads: int
    rating: float
    reviews: List[Dict[str, Any]]
    featured: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Collaboration schemas
class CollaborationMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    user: Optional[str] = None

class CollaborationSessionCreate(BaseModel):
    name: str
    description: Optional[str]

class CollaborationSessionResponse(BaseModel):
    id: str
    name: str
    session_id: str
    created_by: str
    description: Optional[str]
    is_active: bool
    participants: List[str]
    shared_models: List[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Usage statistics schemas
class UsageStatisticsResponse(BaseModel):
    id: str
    user_id: str
    date: datetime
    api_calls: int
    tokens_used: int
    models_tested: int
    code_executions: int
    storage_used: float

    class Config:
        from_attributes = True

# System metrics schemas  
class SystemMetricsResponse(BaseModel):
    id: str
    timestamp: datetime
    active_users: int
    total_requests: int
    avg_response_time: float
    error_rate: float
    cpu_usage: float
    memory_usage: float

    class Config:
        from_attributes = True

# Model comparison schemas
class ModelComparisonRequest(BaseModel):
    model_ids: List[str]
    test_prompt: str
    benchmark_type: str = "general"  # general, code_generation, reasoning, creative

class ModelComparisonResponse(BaseModel):
    comparison_id: str
    results: List[Dict[str, Any]]
    winner: Optional[str]
    metrics: Dict[str, Any]

# Chat history schemas
class ChatHistoryCreate(BaseModel):
    session_id: str
    model_id: Optional[str]
    model_name: str
    messages: List[Dict[str, Any]]
    title: Optional[str]

class ChatHistoryUpdate(BaseModel):
    messages: List[Dict[str, Any]]
    title: Optional[str]

class ChatHistoryResponse(BaseModel):
    id: str
    user_id: Optional[str]
    session_id: str
    model_id: Optional[str]
    model_name: str
    messages: List[Dict[str, Any]]
    title: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Code optimization schemas
class CodeOptimizationRequest(BaseModel):
    code: str
    language: str = "python"

class CodeOptimizationResponse(BaseModel):
    original_code: str
    optimized_code: str
    improvements: List[Dict[str, Any]]
    performance_gain: Optional[float]

class CodeSuggestionResponse(BaseModel):
    suggestion: str
