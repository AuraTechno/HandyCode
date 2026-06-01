"""
Конфигурация AI моделей
"""

MODELS = {
    # DeepSeek модели
    "deepseek": "deepseek/deepseek-chat",
    "deepseek-coder": "deepseek/deepseek-coder",
    "deepseek-r1": "deepseek/deepseek-r1",
    "deepseek-r1-distill": "deepseek/deepseek-r1-distill-qwen-32b",

    # OpenAI модели
    "gpt4": "openai/gpt-4-turbo-preview",
    "gpt4o": "openai/gpt-4o",
    "gpt3": "openai/gpt-3.5-turbo",

    # Anthropic модели
    "claude": "anthropic/claude-3-opus",
    "claude-sonnet": "anthropic/claude-3-sonnet",
    "claude-haiku": "anthropic/claude-3-haiku",

    # Google модели
    "gemini": "google/gemini-pro",
    "gemini-flash": "google/gemini-flash-1.5",

    # Meta модели
    "llama": "meta-llama/llama-3-70b-instruct",
    "llama-8b": "meta-llama/llama-3-8b-instruct",

    # Другие модели
    "mixtral": "mistralai/mixtral-8x7b-instruct",
    "codellama": "codellama/codellama-70b-instruct",
}

MODEL_SETTINGS = {
    "deepseek/deepseek-chat": {
        "temperature": 0.3,
        "max_tokens": 8000,
        "description": "DeepSeek V3 - Универсальный (точный код)"
    },
    "deepseek/deepseek-coder": {
        "temperature": 0.1,
        "max_tokens": 8000,
        "description": "DeepSeek Coder - Код (макс. точность)"
    },
    "deepseek/deepseek-r1": {
        "temperature": 0.5,
        "max_tokens": 4000,
        "description": "DeepSeek R1 - Анализ и архитектура"
    },
    "openai/gpt-4-turbo-preview": {
        "temperature": 0.3,
        "max_tokens": 4000,
        "description": "GPT-4 Turbo"
    },
    "anthropic/claude-3-opus": {
        "temperature": 0.3,
        "max_tokens": 4000,
        "description": "Claude 3 Opus"
    },
    "anthropic/claude-3-sonnet": {
        "temperature": 0.2,
        "max_tokens": 4000,
        "description": "Claude 3 Sonnet"
    },
    "google/gemini-pro": {
        "temperature": 0.4,
        "max_tokens": 4000,
        "description": "Gemini Pro"
    },
    "meta-llama/llama-3-70b-instruct": {
        "temperature": 0.3,
        "max_tokens": 4000,
        "description": "Llama 3 70B"
    },
}

DEFAULT_SETTINGS = {
    "temperature": 0.3,
    "max_tokens": 8000,
    "description": "Универсальная модель"
}


def get_model_settings(model_id: str) -> dict:
    """Получает настройки для конкретной модели"""
    return MODEL_SETTINGS.get(model_id, DEFAULT_SETTINGS)