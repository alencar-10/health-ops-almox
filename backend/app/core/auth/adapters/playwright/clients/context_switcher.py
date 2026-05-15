import logging
from pathlib import Path
from typing import Optional, Dict, Any

from playwright.async_api import Page

from app.core.auth.adapters.playwright.clients.conexao_commit import ConexaoCommitClient
from app.core.auth.adapters.playwright.trace.commit_trace import (
    build_session_snapshot,
    extract_conexao_form_snapshot,
)

logger = logging.getLogger(__name__)

MUN_CONTAINER = "#s2id_seg_operador_codmunicipio"
UNIT_CONTAINER = "#s2id_seg_operador_codunidade"
SECTOR_CONTAINER = "#s2id_seg_operador_codsetor"
BACKEND_ROOT = Path(__file__).resolve().parents[6]


class PlaywrightContextSwitcher:
    """
    Troca transacional de contexto no Vivver: Select2 + commit UJS único + validação fail-closed.
    """

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url.rstrip("/")
        self._commit = ConexaoCommitClient(page)

    async def _select_in_select2(self, container_selector: str, search_text: str) -> bool:
        logger.info("Selecionando '%s' em %s", search_text, container_selector)
        try:
            await self.page.click(f"{container_selector} .select2-choice")
            search_input = ".select2-drop-active .select2-input"
            await self.page.wait_for_selector(search_input, state="visible", timeout=8000)
            await self.page.fill(search_input, search_text)
            result_row = ".select2-drop-active .select2-results .select2-result-selectable"
            try:
                await self.page.wait_for_selector(result_row, timeout=8000)
                await self.page.locator(result_row).first.click()
            except Exception:
                await self.page.keyboard.press("Enter")
            if await self.page.is_visible(search_input):
                await self.page.keyboard.press("Escape")
                return False
            return True
        except Exception as e:
            logger.error("Erro Select2: %s", e)
            return False

    async def _try_lookup_key(
        self,
        lookup_key_id: str,
        hidden_id: str,
        value: str,
        wait_key: Optional[str],
    ) -> bool:
        """Preenche o campo lookup_key (Vivver fwk-lookup-edit-v3) e aguarda hidden."""
        try:
            await self.page.click(f"#{lookup_key_id}")
            await self.page.fill(f"#{lookup_key_id}", value)
            await self.page.press(f"#{lookup_key_id}", "Tab")
            if wait_key:
                await self._wait_lookup(wait_key, timeout_ms=10000)
            return await self.page.input_value(hidden_id) == value
        except Exception as e:
            logger.warning("lookup_key %s: %s", lookup_key_id, e)
            return False

    async def _sync_lookup_keys(self) -> None:
        """Espelha códigos nos lookup_key exigidos pelo POST create_conexao."""
        await self.page.evaluate(
            """() => {
                const pairs = [
                    ['seg_operador_codmunicipio', 'lookup_key_seg_operador_codmunicipio'],
                    ['seg_operador_codunidade', 'lookup_key_seg_operador_codunidade'],
                    ['seg_operador_codsetor', 'lookup_key_seg_operador_codsetor'],
                ];
                for (const [srcId, dstId] of pairs) {
                    const src = document.getElementById(srcId);
                    const dst = document.getElementById(dstId);
                    if (src && dst && src.value) {
                        dst.value = src.value;
                        dst.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                }
            }"""
        )

    async def _wait_lookup(self, key: str, timeout_ms: int = 15000) -> None:
        try:
            await self.page.wait_for_response(
                lambda r: "lookup_edit_v3" in r.url and f"key={key}" in r.url,
                timeout=timeout_ms,
            )
        except Exception:
            logger.warning("Timeout aguardando lookup key=%s", key)

    async def _ensure_hidden(
        self,
        field_id: str,
        expected: str,
        container: str,
        fallbacks: list[str],
        lookup_key_id: Optional[str] = None,
        lookup_wait_key: Optional[str] = None,
    ) -> bool:
        if await self.page.input_value(field_id) == expected:
            return True
        if lookup_key_id and await self._try_lookup_key(
            lookup_key_id, field_id, expected, lookup_wait_key
        ):
            return True
        for term in fallbacks:
            if await self._select_in_select2(container, term):
                if await self.page.input_value(field_id) == expected:
                    return True
        return await self.page.input_value(field_id) == expected

    async def switch(
        self,
        unit_id: str,
        sector_id: Optional[str] = None,
        municipality_id: str = "3128253",
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "success": False,
            "error_code": None,
            "snapshot_before": None,
            "snapshot_after": None,
            "commit": None,
        }

        if sector_id is None or str(sector_id).strip() in ("", "AUTO_RESOLVE"):
            result["error_code"] = "SECTOR_REQUIRED"
            return result
        sector_id = str(sector_id).strip()

        logger.info(
            "Manobra: municipio=%s unidade=%s setor=%s",
            municipality_id,
            unit_id,
            sector_id,
        )

        try:
            if await self.page.query_selector("input#conta") or "/login" in self.page.url:
                result["error_code"] = "AUTH_EXPIRED"
                return result

            before = await build_session_snapshot(self.page, self.base_url)
            result["snapshot_before"] = {
                "header": before.header_context,
                "session_fingerprint": before.session_fingerprint,
            }

            await self.page.goto(
                f"{self.base_url}/seg/operador/conexao",
                timeout=60000,
                wait_until="domcontentloaded",
            )

            if await self.page.query_selector("input#conta"):
                result["error_code"] = "AUTH_EXPIRED"
                return result

            await self.page.wait_for_selector(MUN_CONTAINER, timeout=30000)

            if not await self._ensure_hidden(
                "#seg_operador_codmunicipio",
                municipality_id,
                MUN_CONTAINER,
                ["GUARACIAMA", "GUARACIAMA - MG", municipality_id],
                lookup_key_id="lookup_key_seg_operador_codmunicipio",
                lookup_wait_key="codunidade",
            ):
                result["error_code"] = "MUNICIPALITY_NOT_FOUND"
                await self._save_error(result)
                return result

            await self._wait_lookup("codunidade", timeout_ms=8000)

            if not await self._ensure_hidden(
                "#seg_operador_codunidade",
                unit_id,
                UNIT_CONTAINER,
                [unit_id, "ALMOXARIFADO DA SAUDE", "ALMOXARIFADO"],
                lookup_key_id="lookup_key_seg_operador_codunidade",
                lookup_wait_key="codsetor",
            ):
                # Segunda chance: Tenta o lookup de novo se falhou na primeira
                await self._wait_lookup("codunidade", timeout_ms=5000)
                if not await self.page.input_value("#seg_operador_codunidade") == unit_id:
                    result["error_code"] = "UNIT_NOT_FOUND"
                    await self._save_error(result)
                    return result

            await self._wait_lookup("codsetor", timeout_ms=8000)

            if not await self._ensure_hidden(
                "#seg_operador_codsetor",
                sector_id,
                SECTOR_CONTAINER,
                [sector_id, "ALMOXARIFADO"],
                lookup_key_id="lookup_key_seg_operador_codsetor",
                lookup_wait_key=None,
            ):
                await self._wait_lookup("codsetor", timeout_ms=5000)
                if not await self.page.input_value("#seg_operador_codsetor") == sector_id:
                    result["error_code"] = "SECTOR_NOT_FOUND"
                    await self._save_error(result)
                    return result

            await self._sync_lookup_keys()

            commit_result = await self._commit.commit_with_validation(
                municipality_id, unit_id, sector_id
            )
            result["commit"] = commit_result.to_dict()

            if not commit_result.success:
                result["error_code"] = commit_result.error_code or "COMMIT_FAILED"
                await ConexaoCommitClient.save_failure_artifacts_async(
                    self.page, commit_result, extra=result
                )
                return result

            after = await build_session_snapshot(self.page, self.base_url)
            form = await extract_conexao_form_snapshot(self.page)

            result["snapshot_after"] = {
                "unit": after.header_context.get("unidade")
                or form.select2_labels.get("s2id_seg_operador_codunidade", "N/A"),
                "sector": after.header_context.get("setor")
                or form.select2_labels.get("s2id_seg_operador_codsetor", "N/A"),
                "session_fingerprint": after.session_fingerprint,
            }

            session_changed = (
                before.session_fingerprint != after.session_fingerprint
            )
            if not session_changed:
                result["error_code"] = "SWITCH_NOT_PERSISTED"
                await self._save_error(result)
                return result

            result["success"] = True
            logger.info(
                "Troca persistida: %s | %s",
                result["snapshot_after"]["unit"],
                result["snapshot_after"]["sector"],
            )
            return result

        except Exception as e:
            logger.error("Falha na manobra: %s", e)
            result["error_code"] = "REVALIDATION_FAILED"
            await self._save_error(result)
            return result

    async def _save_error(self, result: Dict[str, Any]) -> None:
        try:
            html = await self.page.content()
            (BACKEND_ROOT / "last_switch_error.html").write_text(html, encoding="utf-8")
        except Exception:
            pass
