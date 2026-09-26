import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "enterprise-rag-super-secret-key-2026")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "enterprise-rag-jwt-secret-key-998877")
    JWT_ACCESS_TOKEN_EXPIRES_HOURS = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "24"))

    # Database configuration: PostgreSQL with SQLite fallback
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    if not DATABASE_URL:
        # Fallback to local SQLite database in data folder
        db_path = os.path.join(BASE_DIR, "data", "enterprise_rag.db")
        DATABASE_URL = f"sqlite:///{db_path}"
    
    # Fix for Heroku/Supabase postgres:// scheme if present
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads & Vector Store paths
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "data", "uploads")
    VECTOR_STORE_PATH = os.path.join(BASE_DIR, "vector_store")

    # AI Model Keys & Options
    LLM_API_KEY = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", os.getenv("GEMINI_API_KEY", "")))
    EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", os.getenv("OPENAI_API_KEY", os.getenv("GEMINI_API_KEY", "")))
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto") # auto, openai, gemini, or local
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # Security Settings
    STRICT_PERMISSION_MODE = os.getenv("STRICT_PERMISSION_MODE", "true").lower() == "true"
    ALLOWED_EXTENSIONS = {"txt", "pdf", "docx", "md"}
