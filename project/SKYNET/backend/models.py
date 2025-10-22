from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer, ForeignKey, JSON, Float, Enum

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from database import Base

def generate_uuid():
    return str(uuid.uuid4())

class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"
    PREMIUM = "premium"

class ModelStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    FAILED = "failed"

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String, default=UserRole.USER.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # User preferences and settings
    preferences = Column(JSON, default={})
    usage_limits = Column(JSON, default={"api_calls": 1000, "storage": 100})
    

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=True)
    provider = Column(String)  # openai, anthropic, gemini, etc.
    encrypted_key = Column(String)  # Encrypted API key
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True))
    usage_count = Column(Integer, default=0)
    

class Model(Base):
    __tablename__ = "models"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # api, custom, fine-tuned
    provider = Column(String)  # openai, anthropic, gemini, custom
    model_identifier = Column(String)  # gpt-4, claude-3, etc.
    file_path = Column(String, nullable=True)
    config = Column(JSON, nullable=True)
    status = Column(String, default="created")  # created, running, stopped, error
    is_public = Column(Boolean, default=False)  # For model marketplace
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=[])
    
    # Performance metrics
    avg_response_time = Column(Float, default=0)
    total_requests = Column(Integer, default=0)
    success_rate = Column(Float, default=100)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    

class TestRun(Base):
    __tablename__ = "test_runs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    model_id = Column(String, ForeignKey("models.id"))
    code = Column(Text)
    prompt = Column(Text, nullable=True)
    results = Column(JSON, nullable=True)  # Test results and metrics
    execution_time = Column(Float)
    status = Column(String, default="pending")  # pending, running, completed, error
    test_type = Column(String)  # unit_test, integration_test, performance_test
    metrics = Column(JSON)  # Store various metrics
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    

class CollaborationSession(Base):
    __tablename__ = "collaboration_sessions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    created_by = Column(String, ForeignKey("users.id"))
    session_id = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    participants = Column(JSON, nullable=True)  # List of user IDs in session
    shared_models = Column(JSON, default=[])  # List of model IDs
    chat_history = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class CodeSession(Base):
    __tablename__ = "code_sessions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=True)
    name = Column(String)
    code = Column(Text)
    language = Column(String, default="python")
    test_code = Column(Text, nullable=True)
    analysis_result = Column(JSON)
    performance_metrics = Column(JSON)
    integrity_check = Column(JSON)
    auto_tests = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    

class PromptTemplate(Base):
    __tablename__ = "prompt_templates"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=True)
    name = Column(String)
    description = Column(Text, nullable=True)
    template = Column(Text)
    variables = Column(JSON, default=[])  # List of variable names
    category = Column(String)
    is_public = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    rating = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    

class ModelBenchmark(Base):
    __tablename__ = "model_benchmarks"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    model_id = Column(String, ForeignKey("models.id"))
    benchmark_name = Column(String)
    score = Column(Float)
    metrics = Column(JSON)  # Detailed metrics
    test_data = Column(JSON)  # Test data used
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    

class ModelMarketplace(Base):
    __tablename__ = "model_marketplace"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    model_id = Column(String, ForeignKey("models.id"), unique=True)
    price = Column(Float, default=0)  # 0 for free models
    downloads = Column(Integer, default=0)
    rating = Column(Float, default=0)
    reviews = Column(JSON, default=[])
    featured = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
class UsageStatistics(Base):
    __tablename__ = "usage_statistics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
    api_calls = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)
    models_tested = Column(Integer, default=0)
    code_executions = Column(Integer, default=0)
    storage_used = Column(Float, default=0)  # in MB
    
class SystemMetrics(Base):
    __tablename__ = "system_metrics"

    id = Column(String, primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    active_users = Column(Integer)
    total_requests = Column(Integer)
    avg_response_time = Column(Float)
    error_rate = Column(Float)
    cpu_usage = Column(Float)
    memory_usage = Column(Float)

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=True)
    session_id = Column(String, index=True)
    model_id = Column(String, ForeignKey("models.id"), nullable=True)
    model_name = Column(String)
    messages = Column(JSON, default=[])
    title = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())