import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str
    api_prefix: str

    # db_host: str
    # db_port: int
    # db_user: str
    # db_name: str
    # db_password: str

    supabase_db_url: str | None = None
    supabase_db_pw: str | None = None
    # ollama_base_url: str
    # ollama_port: int
    # ollama_model: str

    vllm_base_url: str
    vllm_port: int
    vllm_model: str

    embedding_base_url: str
    embedding_port: int
    embedding_model: str
    embedding_dimension: int

    # @property
    # def database_url(self) -> str:
    #     return (
    #         "postgresql+psycopg2://"
    #         f"{self.db_user}:{self.db_password}"
    #         f"@{self.db_host}:{self.db_port}/{self.db_name}"
    #     )


settings = Settings()
