import logging
import asyncio
import uuid
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright

from app.core.auth.engine import AuthEngine, ContextDiscoveryEngine
from app.core.session.context import OperationalContext, SessionContext
from app.core.config import settings

# Importando sub-clientes
from .clients.session_manager import PlaywrightSessionManager
from .clients.discovery_client import PlaywrightDiscoveryClient
from .clients.context_switcher import PlaywrightContextSwitcher
from app.core.auth.operations import OperationStore, OperationStatus
from app.core.auth.adapters.playwright.trace.commit_trace import (
    read_desktop_bar_context,
    read_header_context,
    safe_goto_home,
)

logger = logging.getLogger(__name__)


def _vivver_operator_scope_id() -> Optional[str]:
    raw = (getattr(settings, "VIVVER_OPERATOR_ID", None) or "").strip()
    return raw or None


def _is_missing_label(name: Optional[str]) -> bool:
    return not name or name.strip() in ("N/A", "unknown", "—")

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
        self._browser_lock = asyncio.Lock()
        self._cached_context: Optional[OperationalContext] = None

        # Clientes (Lazy Init após o login)
        self.session = None
        self.discovery = None
        self.switcher = None
        self._last_login_failure: Optional[str] = None

    @property
    def last_login_failure(self) -> Optional[str]:
        """Último erro do fluxo login Playwright/Vivver (para diagnóstico em /session/current)."""
        return self._last_login_failure

    def get_status(self) -> str:
        return self._status

    async def login(self, username: str, password: str, tenant_id: str) -> Optional[OperationalContext]:
        """
        Stage 1 & 2: Authentication & Active Context Resolution
        """
        async with self._browser_lock:
            if self._status == "AUTHENTICATED" and self._page and self._cached_context:
                logger.info("Reutilizando sessão autenticada (cache).")
                return await self._hydrate_context_from_desktop_bar(self._cached_context)

            self._status = "LOGGING_IN"
            logger.info(f"Iniciando login orquestrado: {username}")

            try:
                self._last_login_failure = None
                playwright = await async_playwright().start()
                self._browser = await playwright.chromium.launch(
                    headless=True,
                    args=["--disable-dev-shm-usage", "--no-sandbox"],
                )
                self._context = await self._browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                )
                self._page = await self._context.new_page()

                self.session = PlaywrightSessionManager(self._page)
                self.discovery = PlaywrightDiscoveryClient(self._page, self.base_url)
                self.switcher = PlaywrightContextSwitcher(self._page, self.base_url)

                is_logged_in = await self._page.query_selector(
                    ".desktop, .menu_sistema"
                )
                if not is_logged_in:
                    await self._page.goto(
                        f"{self.base_url}/login",
                        timeout=90000,
                        wait_until="domcontentloaded",
                    )
                    await self._page.fill("input#conta", username)
                    await self._page.fill("input#password", password)
                    await self._page.click("div.btn_entrar")
                    await self._page.wait_for_selector(
                        ".desktop, #desktop, .div_desktop, .menu_sistema",
                        timeout=60000,
                    )
                    logger.info("Login realizado com sucesso.")
                else:
                    logger.info("Sessão já ativa detectada.")

                csrf_token = await self.session.extract_csrf_token()
                cookies = await self.session.get_cookies()
                header = await read_header_context(self._page)
                unit_name = header.get("unidade", "N/A")
                sector_name = header.get("setor", "N/A")
                if _is_missing_label(unit_name) or _is_missing_label(sector_name):
                    logger.warning(
                        "Cabeçalho ERP sem nomes legíveis (unidade=%s setor=%s).",
                        unit_name,
                        sector_name,
                    )

                res_unit_id = "unknown"
                if not _is_missing_label(unit_name):
                    oid = _vivver_operator_scope_id()
                    available_units = await self.discovery.list_units(
                        municipality_id=settings.VITE_MUNICIPALITY_ID,
                        operator_id=oid,
                    )
                    for u in available_units:
                        if u["name"].upper() == unit_name.upper():
                            res_unit_id = u["key"]
                            break
                    if res_unit_id == "unknown":
                        for u in available_units:
                            un = u["name"].upper()
                            if un in unit_name.upper() or unit_name.upper() in un:
                                res_unit_id = u["key"]
                                break

                session_ctx = SessionContext(
                    session_id=cookies.get("_vmx_saude_session"),
                    csrf_token=csrf_token,
                    auth_token=cookies.get("auth_token"),
                    cookies=cookies,
                )
                ctx = OperationalContext(
                    tenant_id=tenant_id,
                    prefecture_name="Guaraciama - MG",
                    unit_id=res_unit_id,
                    unit_name=unit_name,
                    sector_id="0",
                    sector_name=sector_name,
                    operator_id=_vivver_operator_scope_id() or username,
                    operator_name=username,
                    session=session_ctx,
                )
                self._cached_context = ctx
                self._status = "AUTHENTICATED"
                return await self.enrich_context_labels(ctx)

            except Exception as e:
                self._last_login_failure = f"{type(e).__name__}: {e}"
                logger.exception("Erro no orquestrador de login: %s", e)
                self._status = "ERROR"
                return None

    async def _hydrate_context_from_desktop_bar(
        self, ctx: OperationalContext
    ) -> OperationalContext:
        """Sincroniza cache com #unidade_info / #setor_info (evita cache desatualizado)."""
        if not self._page or not ctx:
            return ctx
        try:
            if "/login" in self._page.url or await self._page.query_selector("input#conta"):
                return ctx
            if not await self._page.query_selector("#unidade_info"):
                await safe_goto_home(self._page, self.base_url)
            bar = await read_desktop_bar_context(self._page)
            if bar.get("unit_id"):
                ctx.unit_id = bar["unit_id"]
            if not _is_missing_label(bar.get("unit_name")):
                ctx.unit_name = bar["unit_name"]
            if bar.get("sector_id"):
                ctx.sector_id = bar["sector_id"]
            if not _is_missing_label(bar.get("sector_name")):
                ctx.sector_name = bar["sector_name"]
            self._cached_context = ctx
        except Exception as e:
            logger.warning("Falha ao hidratar contexto da barra ERP: %s", e)
        return await self.enrich_context_labels(ctx)

    async def enrich_context_labels(self, ctx: OperationalContext) -> OperationalContext:
        """Traduz IDs → nomes via Discovery quando o cabeçalho Vivver não expõe labels."""
        if not self.discovery:
            return ctx
        oid = _vivver_operator_scope_id()
        if _is_missing_label(ctx.unit_name) and ctx.unit_id not in ("unknown", "", "0"):
            for u in await self.discovery.list_units(
                municipality_id=settings.VITE_MUNICIPALITY_ID,
                operator_id=oid,
            ):
                if str(u["key"]) == str(ctx.unit_id):
                    ctx.unit_name = u["name"]
                    break
        if _is_missing_label(ctx.sector_name) and ctx.sector_id not in ("", None):
            for s in await self.discovery.list_sectors(
                unit_id=str(ctx.unit_id),
                municipality_id=settings.VITE_MUNICIPALITY_ID,
                operator_id=oid,
            ):
                if str(s["key"]) == str(ctx.sector_id):
                    ctx.sector_name = s["name"]
                    break
        return ctx

    async def get_operational_context(self) -> Optional[OperationalContext]:
        """Retorna contexto em cache se a sessão Playwright ainda está ativa."""
        return await self.login(
            settings.VIVVER_USER,
            settings.VIVVER_PASS,
            settings.VITE_MUNICIPALITY_ID,
        )

    async def _ensure_authenticated(self) -> bool:
        if self.discovery and self._page and self._status == "AUTHENTICATED":
            return True
        return (
            await self.login(
                settings.VIVVER_USER,
                settings.VIVVER_PASS,
                settings.VITE_MUNICIPALITY_ID,
            )
            is not None
        )

    async def list_available_units(self) -> List[Dict]:
        """Stage 3: Access Scope Discovery (Units)"""
        if not await self._ensure_authenticated():
            return []
        oid = _vivver_operator_scope_id()
        return await self.discovery.list_units(
            municipality_id=settings.VITE_MUNICIPALITY_ID,
            operator_id=oid,
        )

    async def list_available_sectors(self, unit_id: str) -> List[Dict]:
        """Stage 3: Access Scope Discovery (Sectors)"""
        if not await self._ensure_authenticated():
            return []
        return await self.discovery.list_sectors(
            unit_id=unit_id,
            municipality_id=settings.VITE_MUNICIPALITY_ID,
            operator_id=_vivver_operator_scope_id(),
        )

    async def switch_context(self, unit_id: str, sector_id: Optional[str] = None, operation_id: Optional[str] = None) -> Optional[OperationalContext]:
        """
        Stage 4 & 5: Switching & Re-Validation
        """
        if not await self._ensure_authenticated():
            if operation_id:
                OperationStore.update(
                    operation_id,
                    status=OperationStatus.FAILED,
                    error="Falha ao autenticar no Vivver.",
                    message="Autenticação ERP falhou.",
                )
            return None

        async with self._browser_lock:
            return await self._switch_context_locked(unit_id, sector_id, operation_id)

    async def _switch_context_locked(
        self, unit_id: str, sector_id: Optional[str], operation_id: Optional[uuid.UUID]
    ) -> Optional[OperationalContext]:
        if not self.switcher or not self._page:
            if operation_id:
                OperationStore.update(
                    operation_id,
                    status=OperationStatus.FAILED,
                    error="Playwright não inicializado.",
                    message="Autenticação ERP falhou.",
                )
            return None

        if operation_id:
            OperationStore.update(
                operation_id,
                status=OperationStatus.SWITCHING,
                message="Executando troca na tela de conexão do Vivver...",
                progress=50,
            )

        municipality_id = settings.VITE_MUNICIPALITY_ID

        # 1. Manobra de Coerência (Stage 4)
        switch_result = await self.switcher.switch(
            unit_id,
            sector_id,
            municipality_id=municipality_id,
        )

        # Clean Slate: no máximo 1 retry após re-login
        if not switch_result["success"] and switch_result["error_code"] == "AUTH_EXPIRED":
            logger.info("Sessão expirada — re-login após liberar lock.")
            self._status = "IDLE"
            if self._browser:
                await self._browser.close()
            self._browser = None
            self._page = None
            self.switcher = None
            self.discovery = None
            # Re-login fora do lock (evita deadlock); caller deve re-invoke switch.
            return None

        if not switch_result["success"]:
            error_code = switch_result["error_code"] or "REVALIDATION_FAILED"
            if operation_id:
                OperationStore.update(
                    operation_id, 
                    status=OperationStatus.FAILED, 
                    error=f"Erro {error_code}: Manobra rejeitada pelo ERP.",
                    metadata={**switch_result}
                )
            return None

        if operation_id:
            OperationStore.update(
                operation_id, 
                status=OperationStatus.VALIDATING, 
                message="Validando novos tokens e integridade pós-troca...",
                metadata={**switch_result}
            )

        # 2. Re-bootstrap dos tokens pós-troca (Stage 5)
        csrf_token = await self.session.extract_csrf_token()
        cookies = await self.session.get_cookies()
        
        # 3. Extração Real do Novo Contexto (Snapshot Final)
        # Usamos os nomes reais que o robô leu na tela após a manobra
        unit_name = switch_result.get("snapshot_after", {}).get("unit", "N/A")
        sector_name = switch_result.get("snapshot_after", {}).get("sector", "N/A")

        await safe_goto_home(self._page, self.base_url)
        bar = await read_desktop_bar_context(self._page)
        if bar.get("unit_id"):
            unit_id = bar["unit_id"]
        if not _is_missing_label(bar.get("unit_name")):
            unit_name = bar["unit_name"]
        if bar.get("sector_id"):
            sector_id = bar["sector_id"]
        if not _is_missing_label(bar.get("sector_name")):
            sector_name = bar["sector_name"]

        header_after = await read_header_context(self._page)
        prefecture_name = header_after.get("municipio", "Guaraciama - MG")
        if _is_missing_label(prefecture_name):
            prefecture_name = "Guaraciama - MG"
        operator_name = "Operador"
        try:
            if await self._page.query_selector(".usuario_nome"):
                operator_name = (await self._page.inner_text(".usuario_nome")).strip()
        except Exception:
            pass

        session_ctx = SessionContext(
            session_id=cookies.get('_vmx_saude_session'),
            csrf_token=csrf_token,
            auth_token=cookies.get('auth_token'),
            cookies=cookies
        )
        
        if operation_id:
            OperationStore.update(operation_id, status=OperationStatus.COMPLETED, message="Troca de contexto concluída com sucesso!")

        ctx = OperationalContext(
            tenant_id=settings.VITE_MUNICIPALITY_ID,
            prefecture_name=prefecture_name,
            unit_id=unit_id,
            unit_name=unit_name,
            sector_id=sector_id or "0",
            sector_name=sector_name,
            operator_id="35304775830",
            operator_name=operator_name,
            session=session_ctx,
        )
        self._cached_context = ctx
        self._status = "AUTHENTICATED"
        return await self._hydrate_context_from_desktop_bar(ctx)

    async def refresh(self, context: OperationalContext) -> bool:
        # Implementação básica de refresh navegando para a Home
        try:
            await safe_goto_home(self._page, self.base_url)
            return True
        except:
            return False
