from app.config import get_settings

settings = get_settings()


def get_llm():
    """
    Returns correct LLM based on LLM_PROVIDER in .env
    Supports: groq | openai | google | ollama
    """
    provider = settings.llm_provider.lower()

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            temperature=0.3,
        )

    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            temperature=0.3,
        )

    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            google_api_key=settings.llm_api_key,
            model=settings.llm_model,
            temperature=0.3,
        )

    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            base_url="http://ollama:11434",
            model=settings.llm_model,
            temperature=0.3,
        )

    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: '{provider}'")