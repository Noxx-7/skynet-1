#!/usr/bin/env python3
"""
Simple test script to verify the backend API endpoints
Run this after docker compose up to test the API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_available_models():
    """Test available models endpoint"""
    print("\n=== Testing Available Models Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/llm/available-models")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Available providers: {list(data.keys())}")
        for provider, models in data.items():
            print(f"  {provider}: {len(models)} models")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_add_api_key(provider="openai", api_key="sk-test123"):
    """Test adding API key"""
    print(f"\n=== Testing Add API Key for {provider} ===")
    try:
        response = requests.post(
            f"{BASE_URL}/llm/api-keys",
            json={"provider": provider, "api_key": api_key}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_list_api_keys():
    """Test listing API keys"""
    print("\n=== Testing List API Keys ===")
    try:
        response = requests.get(f"{BASE_URL}/llm/api-keys")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} API keys")
            for key in data:
                print(f"  - {key['provider']}: Active={key['is_active']}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_list_models():
    """Test listing models"""
    print("\n=== Testing List Models ===")
    try:
        response = requests.get(f"{BASE_URL}/models")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} models")
            for model in data:
                print(f"  - {model['name']} ({model['provider']}) - {model['type']}")
        else:
            print(f"Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing SKYNET Backend API")
    print("=" * 60)

    # Run tests
    results = {
        "Health Check": test_health(),
        "Available Models": test_available_models(),
        "Add API Key": test_add_api_key(),
        "List API Keys": test_list_api_keys(),
        "List Models": test_list_models(),
    }

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test}")

    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")
