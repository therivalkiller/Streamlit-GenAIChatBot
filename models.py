"""
Model configurations for the chatbot
"""

MODELS = {
    "llama-3.1-8b-instant": {
        "id": "llama-3.1-8b-instant",
        "developer": "Meta",
        "description": "Fast 8B Llama model - Great for quick responses",
        "context_window": 131072,
        "max_completion": 131072,
    },
    "llama-3.3-70b-versatile": {
        "id": "llama-3.3-70b-versatile",
        "developer": "Meta",
        "description": "Powerful 70B Llama model - Best for complex tasks",
        "context_window": 131072,
        "max_completion": 32768,
    },
    "meta-llama/llama-guard-4-12b": {
        "id": "meta-llama/llama-guard-4-12b",
        "developer": "Meta",
        "description": "12B Guard model - Content moderation specialist",
        "context_window": 131072,
        "max_completion": 1024,
    },
    "openai/gpt-oss-120b": {
        "id": "openai/gpt-oss-120b",
        "developer": "OpenAI",
        "description": "Large 120B GPT model - Excellent reasoning & creativity",
        "context_window": 131072,
        "max_completion": 65536,
    },
    "openai/gpt-oss-20b": {
        "id": "openai/gpt-oss-20b",
        "developer": "OpenAI",
        "description": "Efficient 20B GPT model - Balanced performance",
        "context_window": 131072,
        "max_completion": 65536,
    },
}

# Default model
DEFAULT_MODEL = "openai/gpt-oss-120b"

def get_model_display_name(model_id: str) -> str:
    """Get formatted display name for model selector"""
    if model_id in MODELS:
        model = MODELS[model_id]
        return f"{model['developer']}: {model['id']} - {model['description']}"
    return model_id

def get_model_info(model_id: str) -> dict:
    """Get model information"""
    return MODELS.get(model_id, {
        "id": model_id,
        "developer": "Unknown",
        "description": "Unknown model",
        "context_window": 0,
        "max_completion": 0,
    })