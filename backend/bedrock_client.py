import json
import os
from typing import Any, List, Dict

import boto3


_client = None


def get_bedrock_client():
    global _client  # noqa: PLW0603
    if _client is None:
        region = os.getenv("AWS_REGION", "us-east-1")
        _client = boto3.client("bedrock-runtime", region_name=region)
    return _client


def call_bedrock(
    prompt: str, 
    custom_logger,
    model_id: str = None,
    system_message: str = None,
    conversation_history: List[Dict] = None
) -> str:
    """
    Universal function that works with ANY Bedrock model
    """
    if model_id is None:
        model_id = os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-pro-v1:0")
        custom_logger.info(f'model id is {model_id}')
        model_id = "us.amazon.nova-pro-v1:0"
    
    client = get_bedrock_client()
    
    # Build messages
    messages = conversation_history.copy() if conversation_history else []
    messages.append({
        "role": "user",
        "content": [{"text": prompt}]
    })
    
    # Prepare request
    request_params = {
        "modelId": model_id,
        "messages": messages,
        "inferenceConfig": {
            "maxTokens": 512,
            "temperature": 0.7,
            "topP": 0.9
        }
    }
    
    # Add system message if provided
    if system_message:
        request_params["system"] = [{"text": system_message}]
    
    try:
        response = client.converse(**request_params)
        return response["output"]["message"]["content"][0]["text"]
        
    except Exception as e:
        print(f"Error with model {model_id}: {e}")
        raise


'''

def test_nova_model_ids():
    prompt = "Hello, how are you?"
    
    # Test different Nova model ID formats
    model_ids_to_test = [
        "us.amazon.nova-pro-v1:0",      # ✅ Inference Profile (try this first)
        "amazon.nova-pro-v1:0",         # Direct model ID
        "us.amazon.nova-lite-v1:0",     # Lite inference profile
        "amazon.nova-lite-v1:0",        # Lite direct model
        "us.amazon.nova-micro-v1:0",    # Micro inference profile
        "amazon.nova-micro-v1:0",       # Micro direct model
    ]
    
    client = get_bedrock_client()
    
    for model_id in model_ids_to_test:
        try:
            print(f"Testing {model_id}...")
            
            response = client.converse(
                modelId=model_id,
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": 100, "temperature": 0.7}
            )
            
            result = response["output"]["message"]["content"][0]["text"]
            print(f"✅ {model_id}: SUCCESS - {result[:50]}...")
            return model_id  # Return the working model ID
            
        except Exception as e:
            print(f"❌ {model_id}: {e}")
    
    print("❌ No Nova models worked")
    return None

# Run the test
working_model_id = test_nova_model_ids()
if working_model_id:
    print(f"\n🎉 Use this model ID: {working_model_id}")

'''