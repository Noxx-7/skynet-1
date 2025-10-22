import os
import json
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import asyncio
import aiohttp
from enum import Enum

class ModelProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    CUSTOM = "custom"
    HUGGINGFACE = "huggingface"
    COHERE = "cohere"
    MISTRAL = "mistral"

class SkynetProvider(ABC):
    """Abstract base class for Skynet providers"""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def stream_generate(self, prompt: str, **kwargs):
        pass

    @abstractmethod
    def validate_api_key(self) -> bool:
        pass

    async def health_check(self, model: str) -> Dict[str, Any]:
        """Check if the model is accessible and working"""
        try:
            response = await self.generate(
                prompt="Hello",
                model=model,
                max_tokens=10,
                temperature=0.1
            )
            return {
                "success": response.get("success", True),
                "available": response.get("success", True),
                "error": response.get("error")
            }
        except Exception as e:
            return {
                "success": False,
                "available": False,
                "error": str(e)
            }

class OpenAIProvider(SkynetProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"
        
    async def generate(self, prompt: str, model: str = "gpt-4o-mini", **kwargs) -> Dict[str, Any]:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 1000)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "response": result["choices"][0]["message"]["content"],
                            "usage": result.get("usage", {}),
                            "model": model
                        }
                    else:
                        error_text = await response.text()
                        try:
                            error_json = json.loads(error_text)
                            error_msg = error_json.get("error", {}).get("message", error_text)
                        except:
                            error_msg = error_text
                        return {
                            "success": False,
                            "error": f"Error calling OpenAI: {error_msg}"
                        }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error calling OpenAI: {str(e)}"
            }
    
    async def stream_generate(self, prompt: str, model: str = "gpt-4o-mini", **kwargs):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "stream": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            ) as response:
                async for line in response.content:
                    if line:
                        line = line.decode('utf-8').strip()
                        if line.startswith("data: "):
                            if line == "data: [DONE]":
                                break
                            try:
                                chunk = json.loads(line[6:])
                                if chunk["choices"][0]["delta"].get("content"):
                                    yield chunk["choices"][0]["delta"]["content"]
                            except:
                                pass
    
    def validate_api_key(self) -> bool:
        return bool(self.api_key and self.api_key.startswith("sk-"))

class AnthropicProvider(SkynetProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1"
        
    async def generate(self, prompt: str, model: str = "claude-3-5-sonnet-20241022", **kwargs) -> Dict[str, Any]:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", 1000),
            "temperature": kwargs.get("temperature", 0.7)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "response": result["content"][0]["text"],
                        "usage": result.get("usage", {}),
                        "model": model
                    }
                else:
                    error = await response.text()
                    return {
                        "success": False,
                        "error": error
                    }
    
    async def stream_generate(self, prompt: str, model: str = "claude-3-5-sonnet-20241022", **kwargs):
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", 1000),
            "temperature": kwargs.get("temperature", 0.7),
            "stream": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=data
            ) as response:
                async for line in response.content:
                    if line:
                        line = line.decode('utf-8').strip()
                        if line.startswith("data: "):
                            try:
                                chunk = json.loads(line[6:])
                                if chunk.get("type") == "content_block_delta":
                                    yield chunk["delta"]["text"]
                            except:
                                pass
    
    def validate_api_key(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 20)

class GeminiProvider(SkynetProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def generate(self, prompt: str, model: str = "gemini-1.5-flash", **kwargs) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.7),
                "maxOutputTokens": kwargs.get("max_tokens", 1000)
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/models/{model}:generateContent?key={self.api_key}",
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "response": result["candidates"][0]["content"]["parts"][0]["text"],
                        "model": model
                    }
                else:
                    error_text = await response.text()
                    try:
                        error_json = json.loads(error_text)
                        error_msg = error_json.get("error", {}).get("message", error_text)
                    except:
                        error_msg = error_text
                    return {
                        "success": False,
                        "error": error_msg
                    }

    async def stream_generate(self, prompt: str, model: str = "gemini-1.5-flash", **kwargs):
        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.7),
                "maxOutputTokens": kwargs.get("max_tokens", 1000)
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/models/{model}:streamGenerateContent?key={self.api_key}",
                headers=headers,
                json=data
            ) as response:
                async for line in response.content:
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            if "candidates" in chunk:
                                text = chunk["candidates"][0]["content"]["parts"][0].get("text", "")
                                if text:
                                    yield text
                        except Exception:
                            pass
    
    def validate_api_key(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 20)

class CustomModelProvider(SkynetProvider):
    """Provider for custom uploaded models"""
    
    def __init__(self, model_path: str, model_type: str = "transformers"):
        self.model_path = model_path
        self.model_type = model_type
        self.model = None
        
    async def load_model(self):
        """Load the custom model from file"""
        pass
        
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        return {
            "success": True,
            "response": f"Custom model response for: {prompt[:50]}...",
            "model": "custom"
        }
    
    async def stream_generate(self, prompt: str, **kwargs):
        response = f"Custom streaming response for: {prompt[:50]}..."
        for char in response:
            yield char
            await asyncio.sleep(0.01)
    
    def validate_api_key(self) -> bool:
        return True

class SkynetProviderFactory:
    """Factory to create Skynet provider instances"""

    @staticmethod
    def create_provider(provider_type: ModelProvider, api_key: Optional[str] = None, **kwargs) -> SkynetProvider:
        if provider_type == ModelProvider.OPENAI:
            return OpenAIProvider(api_key)
        elif provider_type == ModelProvider.ANTHROPIC:
            return AnthropicProvider(api_key)
        elif provider_type == ModelProvider.GEMINI:
            return GeminiProvider(api_key)
        elif provider_type == ModelProvider.CUSTOM:
            return CustomModelProvider(kwargs.get("model_path", ""), kwargs.get("model_type", ""))
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")

class ModelRegistry:
    """Registry for available models and their configurations"""
    
    MODELS = {
        ModelProvider.OPENAI: {
            "gpt-4o": {"name": "GPT-4o", "context": 128000, "vision": True},
            "gpt-4o-mini": {"name": "GPT-4o Mini", "context": 128000, "vision": True},
            "gpt-4-turbo": {"name": "GPT-4 Turbo", "context": 128000, "vision": True},
            "gpt-4": {"name": "GPT-4", "context": 8192, "vision": False},
            "gpt-3.5-turbo": {"name": "GPT-3.5 Turbo", "context": 16384, "vision": False},
            "o1": {"name": "GPT o1", "context": 200000, "vision": False},
            "o1-mini": {"name": "GPT o1-mini", "context": 128000, "vision": False},
        },
        ModelProvider.ANTHROPIC: {
            "claude-3-5-sonnet-20241022": {"name": "Claude 3.5 Sonnet (New)", "context": 200000, "vision": True},
            "claude-3-5-sonnet-20240620": {"name": "Claude 3.5 Sonnet", "context": 200000, "vision": True},
            "claude-3-opus-20240229": {"name": "Claude 3 Opus", "context": 200000, "vision": True},
            "claude-3-sonnet-20240229": {"name": "Claude 3 Sonnet", "context": 200000, "vision": True},
            "claude-3-haiku-20240307": {"name": "Claude 3 Haiku", "context": 200000, "vision": True},
        },
        ModelProvider.GEMINI: {
            "gemini-2.0-flash-exp": {"name": "Gemini 2.0 Flash Exp", "context": 1000000, "vision": True},
        }
    }
    
    @classmethod
    def get_available_models(cls) -> Dict[str, List[Dict[str, Any]]]:
        result = {}
        for provider, models in cls.MODELS.items():
            result[provider.value] = [
                {"id": model_id, **model_info}
                for model_id, model_info in models.items()
            ]
        return result