from app.core.config import settings
from app.core.auth.engine import AuthEngine

class AuthEngineFactory:
    """
    Fábrica responsável por instanciar o motor de autenticação correto.
    IMPLEMENTAÇÃO COM POOL: Garante isolamento por sessão/operador.
    """
    _instances = {}

    @classmethod
    def reset_engine(cls, session_id: str = "default") -> None:
        """Descarta singleton (ex.: após erro Playwright ou troca de .env — reinicie uvicorn se mudou env)."""
        cls._instances.pop(session_id, None)

    @classmethod
    def get_engine(cls, session_id: str = "default") -> AuthEngine:
        if session_id in cls._instances:
            return cls._instances[session_id]

        if settings.APP_MODE == "LAB":
            from app.core.auth.adapters.mock_adapter import MockAuthAdapter
            cls._instances[session_id] = MockAuthAdapter(base_url=settings.VIVVER_URL)
            return cls._instances[session_id]
        
        try:
            from app.core.auth.adapters.playwright.adapter import PlaywrightAuthAdapter
            cls._instances[session_id] = PlaywrightAuthAdapter()
            return cls._instances[session_id]
        except ImportError:
            from app.core.auth.adapters.mock_adapter import MockAuthAdapter
            cls._instances[session_id] = MockAuthAdapter(base_url=settings.VIVVER_URL)
            return cls._instances[session_id]
