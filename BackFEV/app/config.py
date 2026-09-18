from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    DATABASE_URL: str

    JWT_SECRET_KEY: str = "CHANGE_ME_SHARED_ACROSS_SERVICES"
    JWT_ALGORITHM: str = "HS256"


    APP_NAME: str = "HACSA Axis - Operations"
    API_V1_PREFIX: str = "/api/v1"

    # Allow our frontend to communicate with the backend.
    CORS_ORIGINS: list[str] = ["*"]

    
    # Occupancy
    
    # Alert when a venue reaches 85% of its capacity.
    OCCUPANCY_ELEVATED_THRESHOLD: float = 0.85

    # Critical alert when a venue reaches 98% of its capacity.
    OCCUPANCY_CRITICAL_THRESHOLD: float = 0.98

   
    # Incident Escalation
    # How long an unresolved incident can remain
    # before the system flags it for escalation.

    ESCALATION_MINUTES_CRITICAL: int = 5
    ESCALATION_MINUTES_HIGH: int = 10
    ESCALATION_MINUTES_MEDIUM: int = 25
    ESCALATION_MINUTES_LOW: int = 40

   
    class Config:
        env_file = ".env"


# Create our settings object.
settings = Settings()