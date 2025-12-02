from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    environment: str = "development"
    
    # Kubernetes configuration
    k8s_config_path: str | None = None  # Path to kubeconfig file, None for auto-detect
    kubeconfig: str | None = None  # Alternative env var name
    
    # Agent platform file system configuration
    agent_platform_base_path: str = "/var/agent-platform"
    
    # Aegra configuration
    aegra_json_path: str = "/var/agent-platform/aegra/aegra.json"  # Path to aegra.json file (backend service path)
    aegra_api_base_url: str = "http://localhost:8001"  # Aegra API base URL for internal Docker communication (override with AEGRA_API_BASE_URL env var)
    aegra_api_public_url: str = "http://localhost:8001"  # Aegra API base URL for end users (override with AEGRA_API_PUBLIC_URL env var)
    chat_ui_base_url: str = "http://localhost:3002"  # Agent Chat UI base URL
    
    # Ingress configuration
    ingress_host: str = "agents.yourdomain.com"  # Hostname for ingress rules

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

