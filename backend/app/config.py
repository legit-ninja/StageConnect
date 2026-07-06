from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://stageconnect:stageconnect@localhost:5432/stageconnect"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:3000"
    environment: str = "development"

    admin_email: str = ""
    admin_password: str = ""

    payments_enabled: bool = False
    cancellation_cutoff_hours: int = 48

    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_connect_client_id: str = ""
    platform_commission_percent: int = 10

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = ""
    facebook_app_id: str = ""
    facebook_app_secret: str = ""
    facebook_redirect_uri: str = ""
    frontend_oauth_success_url: str = "http://localhost:3000/auth/callback"
    frontend_oauth_error_url: str = "http://localhost:3000/auth/error"

    service_area_default_lat: float = 36.2168
    service_area_default_lng: float = -81.6746
    service_area_default_radius_km: float = 80.0
    seed_dev_data: bool = False

    upload_root: str = "uploads"
    public_upload_base_url: str = "http://localhost:8000/uploads"
    photo_moderation_enabled: bool = False
    frontend_base_url: str = "http://localhost:3000"

    weather_timezone: str = "America/New_York"
    weather_cache_ttl_seconds: int = 10800

    service_area_default_secret: str = "dev-change-me"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
