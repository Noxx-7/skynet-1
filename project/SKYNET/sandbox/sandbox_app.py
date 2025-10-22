from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import sys
import os
import importlib.util
from typing import Any, Dict

app = FastAPI(title="LLM Sandbox")

class CodeExecutionRequest(BaseModel):
    code: str
    timeout: int = 30

class TestRequest(BaseModel):
    test_code: str
    model_wrapper: str

@app.post("/execute")
async def execute_code(request: CodeExecutionRequest):
    """Execute Python code safely in sandbox"""
    try:
        # Write code to temporary file
        with open("/tmp/temp_code.py", "w") as f:
            f.write(request.code)
        
        # Execute with timeout and resource limits
        result = subprocess.run([
            "timeout", str(request.timeout),
            "python", "/tmp/temp_code.py"
        ], capture_output=True, text=True, cwd="/home/llmuser/workspace")
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
            "return_code": result.returncode
        }
        
    except Exception as e:
        return {
            "success": False,
            "output": None,
            "error": str(e),
            "return_code": -1
        }

@app.post("/test")
async def run_tests(request: TestRequest):
    """Run tests on model wrapper"""
    try:
        # Save model wrapper
        with open("/tmp/model_wrapper.py", "w") as f:
            f.write(request.model_wrapper)
        
        # Save test code
        with open("/tmp/test_model.py", "w") as f:
            f.write(request.test_code)
        
        # Run tests
        result = subprocess.run([
            "python", "-m", "pytest", "/tmp/test_model.py", "-v"
        ], capture_output=True, text=True)
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }
        
    except Exception as e:
        return {
            "success": False,
            "output": None,
            "error": str(e)
        }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "llm-sandbox"}