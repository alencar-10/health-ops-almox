import logging
import asyncio
from typing import Optional, List, Dict
from playwright.async_api import async_playwright

from app.core.auth.engine import AuthEngine, ContextDiscoveryEngine
from app.core.session.context import OperationalContext, SessionContext
from app.core.config import settings

# Importando sub-clientes
from .clients.session_manager import PlaywrightSessionManager
from .clients.discovery_client import PlaywrightDiscoveryClient
from .clients.context_switcher import PlaywrightContextSwitcher

logger = logging.getLogger(__name__)

class PlaywrightAuthAdapter(AuthEngine, ContextDiscoveryEngine):
    """
    Orquestrador Playwright para Autenticação e Descoberta de Contexto.
    Segue o OPERATIONAL_LIFECYCLE e as CONTEXT_INTEGRITY_RULES.
    """
    
    def __init__(self):
        self.base_url = "https://guaraciama-mg.vivver.com"
        self._status = "IDLE"
        self._browser = None
        self._context = None
        self._page = None
        
        # Clientes (Lazy Init após o login)
        self.session = None
        self.discovery = None
        self.switcher = None

    def get_status(self) -> str:
        return self._status

    async def login(self, username: str, password: str, tenant_id: str) -> Optional[OperationalContext]:
        """
        Stage 1 & 2: Authentication & Active Context Resolution
        """
        self._status = "LOGGING_IN"
        logger.info(f"Iniciando login orquestrado: {username}")
        
        playwright = await async_playwright().start()
        self._browser = await playwright.chromium.launch(headless=True)
        self._context = await self._browser.new_context()
        self._page = await self._context.new_page()

        # Inicializa Sub-clientes
        self.session = PlaywrightSessionManager(self._page)
        self.discovery = PlaywrightDiscoveryClient(self._page, self.base_url)
        self.switcher = PlaywrightContextSwitcher(self._page, self.base_url)

        try:
            # 1. Login
            await self._page.goto(f"{self.base_url}/login")
            await self._page.fill('input#conta', username)
            await self._page.fill('input#password', password)
            await self._page.click('div.btn_entrar') 
            await self._page.wait_for_load_state("networkidle")

            # 2. Captura Inicial (Active Context Resolution)
            csrf_token = await self.session.extract_csrf_token()
            cookies = await self.session.get_cookies()
            session_id = cookies.get('_vmx_saude_session')

            if not session_id:
                logger.error("Falha no bootstrap da sessão.")
                return None

            # Resolução visual rápida do contexto ativo (Stage 2)
            # Nota: Usamos fallbacks pois o discovery completo (Stage 3) é disparado sob demanda
            self._status = "AUTHENTICATED"
            
            session_ctx = SessionContext(
                session_id=session_id,
                csrf_token=csrf_token,
                auth_token=cookies.get('auth_token'),
                cookies=cookies
            )
            
            return OperationalContext(
                tenant_id=tenant_id,
                prefecture_name="Guaraciama - MG",
                unit_id="10", # Fallback inicial
                unit_name="UBS SAO JOAO BATISTA PLANTOES",
                sector_id="0",
                sector_name="ATENDIMENTO",
                operator_id=username,
                operator_name="Administrador",
                session=session_ctx
            )

        except Exception as e:
            logger.error(f"Erro no orquestrador de login: {str(e)}")
            self._status = "ERROR"
            return None

    async def list_available_units(self) -> List[Dict]:
        """Stage 3: Access Scope Discovery (Units)"""
        if not self.discovery:
            return []
        # Para Guaraciama usamos o ID fixo ou injetado
        return await self.discovery.list_units(municipality_id="3128253")

    async def list_available_sectors(self, unit_id: str) -> List[Dict]:
        """Stage 3: Access Scope Discovery (Sectors)"""
        if not self.discovery:
            return []
        return await self.discovery.list_sectors(unit_id=unit_id)

    async def switch_context(self, unit_id: str, sector_id: str) -> Optional[OperationalContext]:
        """
        Stage 4 & 5: Switching & Re-Validation
        """
        if not self.switcher:
            return None
            
        success = await self.switcher.switch(unit_id, sector_id)
        if not success:
            return None

        # Re-bootstrap dos tokens pós-troca (Stage 5)
        csrf_token = await self.session.extract_csrf_token()
        cookies = await self.session.get_cookies()
        
        session_ctx = SessionContext(
            session_id=cookies.get('_vmx_saude_session'),
            csrf_token=csrf_token,
            auth_token=cookies.get('auth_token'),
            cookies=cookies
        )
        
        # Retorna o novo contexto validado
        return OperationalContext(
            tenant_id="3128253",
            prefecture_name="Guaraciama - MG",
            unit_id=unit_id,
            unit_name="UNIDADE ATUALIZADA", # Poderíamos extrair dinamicamente aqui
            sector_id=sector_id,
            sector_name="SETOR ATUALIZADO",
            operator_id="35304775830",
            operator_name="Administrador",
            session=session_ctx
        )

    async def refresh(self, context: OperationalContext) -> bool:
        # Implementação básica de refresh navegando para a Home
        try:
            await self._page.goto(f"{self.base_url}/")
            return True
        except:
            return False
