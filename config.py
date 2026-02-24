import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    PDLOR_DOLLAR_PER_BBL = float(os.getenv("PDLOR_DOLLAR_PER_BBL", "19"))
    PDLOR_APC_PRODUCTION_LOST = float(os.getenv("PDLOR_APC_PRODUCTION_LOST", "84942"))
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB
    SESSION_TYPE = "filesystem"
    SESSION_FILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flask_session")
    SESSION_PERMANENT = False
