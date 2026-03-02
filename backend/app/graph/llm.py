from langchain_core.language_models import BaseChatModel

from app.config import settings


def get_llm() -> BaseChatModel:
    provider = settings.llm_provider.lower()

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(api_key=settings.groq_api_key, model="llama-3.3-70b-versatile")
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(api_key=settings.openai_api_key, model="gpt-4o")
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(api_key=settings.anthropic_api_key, model="claude-haiku-4-5-20251001")
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
