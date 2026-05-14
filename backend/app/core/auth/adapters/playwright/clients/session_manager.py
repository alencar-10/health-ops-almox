import logging
from typing import Dict, Optional
from playwright.async_api import Page

logger = logging.getLogger(__name__)

class PlaywrightSessionManager:
    """
    Responsável por gerenciar o estado técnico da sessão (Cookies, Tokens, CSRF).
    """
    def __init__(self, page: Page):
        self.page = page

    async def get_cookies(self) -> Dict[str, str]:
        """Extrai cookies ativos da página."""
        cookies = await self.page.context.cookies()
        return {c['name']: c['value'] for c in cookies}

    async def extract_csrf_token(self) -> Optional[str]:
        """Extrai o CSRF token do meta tag (padrão Rails/Vivver)."""
        try:
                        csrf_token = await self.page.eval_on_selector(
                            'meta[name="csrf-token"]', 
                            'el => el.content'
                        )
                        return csrf_token
        except Exception:
            logger.warning("CSRF Token não encontrado na página atual.")
            return None

    async def get_session_version(self) -> str:
        """
        Gera um hash ou versão baseada no cookie de sessão e CSRF
        para detectar mudanças de estado.
        """
        cookies = await self.get_cookies()
        session_id = cookies.get('_vmx_saude_session', '')
        csrf = await self.extract_csrf_token() or ''
        return f"{session_id[-8:]}:{csrf[-8:]}"
