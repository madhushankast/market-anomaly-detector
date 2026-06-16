import os

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://adminmst:adminpass@db:5432/market_db")

# This exact line MUST exist so app/db/session.py can import it!
settings = Settings()