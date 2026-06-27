from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "CivicPulse"
    API_V1_STR: str = "/api/v1"
    
    DB_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    GEMINI_API_KEY: str
    OPENROUTER_API_KEY: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    STORAGE_BACKEND: str = "local"
    CLOUDINARY_URL: str = ""
    
    @property
    def FRONTEND_URL(self) -> str:
        return "https://civic-pulse-qxgmy0td4-islamrafatul004-8764s-projects.vercel.app"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
