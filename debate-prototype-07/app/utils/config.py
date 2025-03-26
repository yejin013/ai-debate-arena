import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langfuse import Langfuse

# .env 파일에서 환경 변수 로드
load_dotenv()


def get_llm():
    return AzureChatOpenAI(
        openai_api_key=os.getenv("AOAI_API_KEY"),
        azure_endpoint=os.getenv("AOAI_ENDPOINT"),
        azure_deployment=os.getenv("AOAI_DEPLOY_GPT4O"),
        api_version=os.getenv("AOAI_API_VERSION"),
        temperature=0.7,
    )


def get_embeddings():
    return AzureOpenAIEmbeddings(
        model=os.getenv("AOAI_EMBEDDING_DEPLOYMENT"),
        openai_api_version=os.getenv("AOAI_API_VERSION"),
        api_key=os.getenv("AOAI_API_KEY"),
        azure_endpoint=os.getenv("AOAI_ENDPOINT"),
    )


def get_langfuse():
    return Langfuse(
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        host=os.getenv("LANGFUSE_HOST"),
    )


langfuse = get_langfuse()
