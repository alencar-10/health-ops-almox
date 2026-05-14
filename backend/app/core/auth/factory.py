from app.core.config import settings
from app.core.auth.engine import AuthEngine

class AuthEngineFactory:
    """
    Fábrica responsável por instanciar o motor de autenticação correto.
    IMPLEMENTAÇÃO COM HARDENING: Imports dinâmicos para evitar contaminação de dependências.
    """

    @staticmethod
    def get_engine() -> AuthEngine:
        # TESTE DE HARDENING: Usando o Mock para provar o desacoplamento
        # Note que não importamos o Playwright no topo do arquivo.
        
        if settings.APP_MODE == "LAB":
            from app.core.auth.adapters.mock_adapter import MockAuthAdapter
            return MockAuthAdapter(base_url=settings.VIVVER_URL)
        
        # Se chegarmos aqui, tentamos carregar o Playwright apenas sob demanda
        try:
            from app.core.auth.adapters.playwright.adapter import PlaywrightAuthAdapter
            return PlaywrightAuthAdapter(base_url=settings.VIVVER_URL)
        except ImportError:
            # Fallback seguro caso o Playwright não esteja instalado no ambiente
            from app.core.auth.adapters.mock_adapter import MockAuthAdapter
            return MockAuthAdapter(base_url=settings.VIVVER_URL)
