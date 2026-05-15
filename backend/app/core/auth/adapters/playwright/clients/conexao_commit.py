"""
Commit transacional da troca de contexto Vivver (create_conexao).
Baseado na forense Fase 1 — COMMIT_PROTOCOL.md.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from playwright.async_api import Page

from app.core.auth.adapters.playwright.trace.commit_trace import (
    extract_conexao_form_snapshot,
)

logger = logging.getLogger(__name__)

SUBMIT_BTN = "#seg_operador_conexao_btn_submit"
SUCCESS_MARKER = "Conexão ativada com sucesso"
BACKEND_ROOT = Path(__file__).resolve().parents[6]

REQUIRED_HIDDEN = (
    "seg_operador[codoperador]",
    "seg_operador[codmunicipio]",
    "seg_operador[codunidade]",
    "seg_operador[codsetor]",
)
REQUIRED_LOOKUP_KEYS = (
    "lookup_key[seg_operador[codmunicipio]]",
    "lookup_key[seg_operador[codunidade]]",
    "lookup_key[seg_operador[codsetor]]",
)


@dataclass
class CommitResult:
    success: bool
    error_code: Optional[str] = None
    http_status: Optional[int] = None
    response_snippet: Optional[str] = None
    post_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "error_code": self.error_code,
            "http_status": self.http_status,
            "response_snippet": self.response_snippet,
            "post_count": self.post_count,
        }


class ConexaoCommitClient:
    """Dispara e valida o POST UJS único de create_conexao."""

    def __init__(self, page: Page):
        self.page = page
        self._post_count = 0

    async def validate_form_ready(
        self,
        municipality_id: str,
        unit_id: str,
        sector_id: str,
    ) -> tuple[bool, Optional[str], dict[str, str]]:
        form = await extract_conexao_form_snapshot(self.page)
        hidden = form.hidden_fields

        for key in REQUIRED_HIDDEN + REQUIRED_LOOKUP_KEYS:
            if key not in hidden or hidden[key] == "":
                return False, f"MISSING_FIELD:{key}", hidden

        if hidden["seg_operador[codmunicipio]"] != municipality_id:
            return False, "MUNICIPALITY_MISMATCH", hidden
        if hidden["seg_operador[codunidade]"] != unit_id:
            return False, "UNIT_MISMATCH", hidden
        if hidden["seg_operador[codsetor]"] != sector_id:
            return False, "SECTOR_MISMATCH", hidden
        if not form.csrf_meta:
            return False, "CSRF_META_MISSING", hidden

        return True, None, hidden

    async def commit(self, timeout_ms: int = 30000) -> CommitResult:
        try:
            async with self.page.expect_response(
                lambda r: (
                    "create_conexao" in r.url
                    and r.request.method == "POST"
                    and r.request.resource_type == "xhr"
                ),
                timeout=timeout_ms,
            ) as resp_info:
                await self.page.click(SUBMIT_BTN)
            response = await resp_info.value
            body = await response.text()
            status = response.status

            if status >= 400:
                return CommitResult(
                    success=False,
                    error_code="COMMIT_REJECTED",
                    http_status=status,
                    response_snippet=body[:500],
                    post_count=1,
                )

            if SUCCESS_MARKER not in body:
                return CommitResult(
                    success=False,
                    error_code="COMMIT_RESPONSE_INVALID",
                    http_status=status,
                    response_snippet=body[:500],
                    post_count=1,
                )

            return CommitResult(
                success=True,
                http_status=status,
                response_snippet=body[:200],
                post_count=1,
            )
        except Exception as exc:
            logger.error("Commit create_conexao falhou: %s", exc)
            return CommitResult(success=False, error_code="COMMIT_NOT_SENT", post_count=0)

    async def commit_with_validation(
        self,
        municipality_id: str,
        unit_id: str,
        sector_id: str,
    ) -> CommitResult:
        ready, err, hidden = await self.validate_form_ready(
            municipality_id, unit_id, sector_id
        )
        if not ready:
            logger.error("Formulário não pronto para commit: %s", err)
            return CommitResult(success=False, error_code=err or "FORM_NOT_READY")

        return await self.commit()

    @staticmethod
    async def save_failure_artifacts_async(
        page: Page,
        commit_result: CommitResult,
        extra: Optional[dict[str, Any]] = None,
    ) -> None:
        backend_root = BACKEND_ROOT
        try:
            html = await page.content()
            (backend_root / "last_switch_error.html").write_text(html, encoding="utf-8")
        except Exception:
            pass
        payload = {**commit_result.to_dict(), **(extra or {})}
        (backend_root / "last_switch_commit.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
