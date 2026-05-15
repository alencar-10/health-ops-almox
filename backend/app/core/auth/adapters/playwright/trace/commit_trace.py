"""
Forensic helpers for Vivver context-switch commit (create_conexao).
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs

from playwright.async_api import Page, Request, Response


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def safe_goto_home(page: Page, base_url: str, *, timeout_ms: int = 60000) -> None:
    """Navigate to Vivver home without failing on interrupted loads (ERR_ABORTED)."""
    home = f"{base_url.rstrip('/')}/"
    try:
        if page.url.rstrip("/") == base_url.rstrip("/"):
            await page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
            if await page.query_selector("#unidade_info"):
                return
        await page.goto(home, wait_until="domcontentloaded", timeout=timeout_ms)
    except Exception as exc:
        if "ERR_ABORTED" not in str(exc):
            raise
        await page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)


def _truncate(text: Optional[str], limit: int = 2048) -> Optional[str]:
    if text is None:
        return None
    if len(text) <= limit:
        return text
    return text[:limit] + f"... [truncated, total={len(text)}]"


def _parse_form_body(post_data: Optional[str]) -> dict[str, list[str]]:
    if not post_data:
        return {}
    return parse_qs(post_data, keep_blank_values=True)


@dataclass
class NetworkEvent:
    ts: str
    phase: str
    url: str
    method: str
    status: Optional[int] = None
    resource_type: Optional[str] = None
    request_headers: dict[str, str] = field(default_factory=dict)
    response_headers: dict[str, str] = field(default_factory=dict)
    post_data: Optional[str] = None
    post_data_parsed: dict[str, list[str]] = field(default_factory=dict)
    response_body_preview: Optional[str] = None
    failure: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FormSnapshot:
    ts: str
    page_url: str
    form_action: Optional[str]
    form_method: Optional[str]
    data_remote: Optional[str]
    csrf_meta: Optional[str]
    authenticity_token_in_form: Optional[str]
    hidden_fields: dict[str, str]
    select2_labels: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SessionSnapshot:
    ts: str
    cookies: dict[str, str]
    session_fingerprint: str
    header_context: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CommitTraceCollector:
    INTERESTING_URL = re.compile(
        r"(create_conexao|lookup_edit_v3|/seg/operador|/login)",
        re.I,
    )

    def __init__(self, label: str):
        self.label = label
        self.events: list[NetworkEvent] = []
        self.timeline: list[dict[str, Any]] = []

    def _log_timeline(self, event: str, **kwargs: Any) -> None:
        self.timeline.append({"ts": _utc_now(), "event": event, **kwargs})

    def attach(self, page: Page) -> None:
        def on_request(request: Request) -> None:
            if not self.INTERESTING_URL.search(request.url):
                return
            headers = {k.lower(): v for k, v in request.headers.items()}
            post = request.post_data
            self.events.append(
                NetworkEvent(
                    ts=_utc_now(),
                    phase="request",
                    url=request.url,
                    method=request.method,
                    resource_type=request.resource_type,
                    request_headers={
                        k: headers[k]
                        for k in (
                            "x-csrf-token",
                            "x-requested-with",
                            "content-type",
                            "accept",
                        )
                        if k in headers
                    },
                    post_data=_truncate(post),
                    post_data_parsed=_parse_form_body(post),
                )
            )
            self._log_timeline(
                "http_request",
                method=request.method,
                url=request.url,
                has_post=bool(post),
            )

        async def on_response(response: Response) -> None:
            if not self.INTERESTING_URL.search(response.url):
                return
            try:
                body = await response.text()
            except Exception as exc:
                body = f"<unreadable: {exc}>"
            headers = {k.lower(): v for k, v in response.headers.items()}
            post = response.request.post_data
            self.events.append(
                NetworkEvent(
                    ts=_utc_now(),
                    phase="response",
                    url=response.url,
                    method=response.request.method,
                    status=response.status,
                    resource_type=response.request.resource_type,
                    response_headers={
                        k: headers[k]
                        for k in ("content-type", "location", "x-request-id")
                        if k in headers
                    },
                    post_data=_truncate(post),
                    post_data_parsed=_parse_form_body(post),
                    response_body_preview=_truncate(body),
                )
            )
            self._log_timeline(
                "http_response",
                method=response.request.method,
                url=response.url,
                status=response.status,
            )

        def on_failed(request: Request) -> None:
            if not self.INTERESTING_URL.search(request.url):
                return
            self.events.append(
                NetworkEvent(
                    ts=_utc_now(),
                    phase="failed",
                    url=request.url,
                    method=request.method,
                    failure=request.failure,
                )
            )
            self._log_timeline("http_failed", url=request.url, failure=request.failure)

        page.on("request", on_request)
        page.on("response", on_response)
        page.on("requestfailed", on_failed)

    def find_create_conexao(self) -> list[NetworkEvent]:
        return [e for e in self.events if "create_conexao" in e.url.lower()]

    def summary(self) -> dict[str, Any]:
        commits = self.find_create_conexao()
        posts = [e for e in commits if e.phase == "request" and e.method == "POST"]
        responses = [e for e in commits if e.phase == "response"]
        return {
            "label": self.label,
            "total_events": len(self.events),
            "create_conexao_post_count": len(posts),
            "create_conexao_response_count": len(responses),
            "create_conexao_posts": [e.to_dict() for e in posts],
            "create_conexao_responses": [e.to_dict() for e in responses],
            "lookup_xhr_count": len(
                [
                    e
                    for e in self.events
                    if "lookup_edit_v3" in e.url and e.phase == "response"
                ]
            ),
        }

    def save(self, path: Path, extra: Optional[dict[str, Any]] = None) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "label": self.label,
            "summary": self.summary(),
            "timeline": self.timeline,
            "events": [e.to_dict() for e in self.events],
        }
        if extra:
            payload.update(extra)
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )


async def extract_conexao_form_snapshot(page: Page) -> FormSnapshot:
    data = await page.evaluate(
        """() => {
            const form = document.querySelector('form.edit_seg_operador');
            const meta = document.querySelector('meta[name="csrf-token"]');
            const hidden = {};
            if (form) {
                form.querySelectorAll('input').forEach((el) => {
                    if (el.name && el.type !== 'submit') {
                        hidden[el.name] = el.value ?? '';
                    }
                });
            }
            const labels = {};
            document.querySelectorAll('[id^="s2id_seg_operador_"]').forEach((container) => {
                const chosen = container.querySelector('.select2-chosen');
                if (chosen) labels[container.id] = chosen.textContent.trim();
            });
            const tokenInput = form?.querySelector('input[name="authenticity_token"]');
            return {
                page_url: location.href,
                form_action: form?.getAttribute('action') ?? null,
                form_method: form?.getAttribute('method') ?? null,
                data_remote: form?.getAttribute('data-remote') ?? null,
                csrf_meta: meta?.getAttribute('content') ?? null,
                authenticity_token_in_form: tokenInput?.value ?? null,
                hidden_fields: hidden,
                select2_labels: labels,
            };
        }"""
    )
    return FormSnapshot(ts=_utc_now(), **data)


_BAR_LINE_RE = re.compile(r"^(\d+)\s*-\s*(.+)$")


def parse_vivver_bar_line(text: str) -> tuple[Optional[str], str]:
    """'14 - ALMOXARIFADO DA SAUDE' -> ('14', 'ALMOXARIFADO DA SAUDE')."""
    raw = (text or "").strip()
    if not raw:
        return None, "N/A"
    match = _BAR_LINE_RE.match(raw)
    if match:
        return match.group(1), match.group(2).strip()
    return None, raw


def _strip_vivver_code_prefix(label: str) -> str:
    """'14 - ALMOXARIFADO DA SAUDE' -> 'ALMOXARIFADO DA SAUDE'."""
    text = label.strip()
    if not text or text == "N/A":
        return text or "N/A"
    if " - " in text:
        return text.split(" - ", 1)[1].strip()
    return text


_HEADER_JS = """() => {
    const pick = (selectors) => {
        for (const sel of selectors) {
            const el = document.querySelector(sel);
            const text = el?.textContent?.replace(/\\s+/g, ' ').trim();
            if (text && text.length > 1) return text;
        }
        return null;
    };
    const stripCode = (text) => {
        if (!text) return text;
        const idx = text.indexOf(' - ');
        return idx >= 0 ? text.slice(idx + 3).trim() : text;
    };

    const municipio = pick([
        '#municipio_info', '.municipio_nome', '#municipio_nome', '.nom_municipio',
        '#lblMunicipio', '.lbl-municipio', '[data-context="municipio"]',
    ]);
    const unidade = pick([
        '#unidade_info', '#bar_bottom #unidade_info', '.bottom_right #unidade_info',
        '.unidade_nome', '#unidade_nome', '.nom_unidade', '#lblUnidade',
        '.lbl-unidade', '.contexto-unidade', '[data-context="unidade"]',
        '#s2id_seg_operador_codunidade .select2-chosen',
    ]);
    const setor = pick([
        '#setor_info', '#bar_bottom #setor_info', '.bottom_right #setor_info',
        '.setor_nome', '#setor_nome', '.nom_setor', '#lblSetor',
        '.lbl-setor', '.contexto-setor', '[data-context="setor"]',
        '#s2id_seg_operador_codsetor .select2-chosen',
    ]);

    const scanLabeledRows = () => {
        const out = { municipio: null, unidade: null, setor: null };
        const labels = [
            ['municipio', /munic[ií]pio/i],
            ['unidade', /unidade/i],
            ['setor', /setor/i],
        ];
        const nodes = document.querySelectorAll(
            '.desktop label, .desktop .label, .menu_sistema label, ' +
            '.barra-superior label, .navbar label, .header label, .topo label'
        );
        for (const node of nodes) {
            const labelText = node.textContent?.trim() || '';
            for (const [key, re] of labels) {
                if (!out[key] && re.test(labelText)) {
                    const row = node.closest('tr, .row, .form-group, li, div');
                    const valueEl = row?.querySelector(
                        'span:not(label), strong, b, .value, .nome, a'
                    );
                    const val = valueEl?.textContent?.replace(/\\s+/g, ' ').trim();
                    if (val && val.length > 1 && !re.test(val)) out[key] = val;
                }
            }
        }
        return out;
    };

    const labeled = scanLabeledRows();
    return {
        municipio: municipio || labeled.municipio || 'N/A',
        unidade: stripCode(unidade || labeled.unidade) || 'N/A',
        setor: stripCode(setor || labeled.setor) || 'N/A',
    };
}"""


async def read_desktop_bar_context(page: Page) -> dict[str, str]:
    """Lê barra inferior do desktop com código + nome (fonte soberana pós-switch)."""
    result = {
        "unit_id": "",
        "unit_name": "N/A",
        "sector_id": "",
        "sector_name": "N/A",
    }
    try:
        unit_raw = ""
        sector_raw = ""
        if await page.query_selector("#unidade_info"):
            unit_raw = (await page.inner_text("#unidade_info")).strip()
        if await page.query_selector("#setor_info"):
            sector_raw = (await page.inner_text("#setor_info")).strip()
        uid, un = parse_vivver_bar_line(unit_raw)
        sid, sn = parse_vivver_bar_line(sector_raw)
        if uid:
            result["unit_id"] = uid
        if un and un != "N/A":
            result["unit_name"] = un
        if sid:
            result["sector_id"] = sid
        if sn and sn != "N/A":
            result["sector_name"] = sn
    except Exception:
        pass
    header = await read_header_context(page)
    if result["unit_name"] == "N/A" and header.get("unidade") not in (None, "N/A"):
        result["unit_name"] = header["unidade"]
    if result["sector_name"] == "N/A" and header.get("setor") not in (None, "N/A"):
        result["sector_name"] = header["setor"]
    return result


async def read_header_context(page: Page) -> dict[str, str]:
    """Lê unidade/setor/município do desktop Vivver (múltiplos seletores + scan por label)."""
    try:
        data = await page.evaluate(_HEADER_JS)
        if isinstance(data, dict):
            return {
                "municipio": (data.get("municipio") or "N/A").strip(),
                "unidade": _strip_vivver_code_prefix(data.get("unidade") or "N/A"),
                "setor": _strip_vivver_code_prefix(data.get("setor") or "N/A"),
            }
    except Exception:
        pass
    return {"municipio": "N/A", "unidade": "N/A", "setor": "N/A"}


async def build_session_snapshot(page: Page, base_url: str) -> SessionSnapshot:
    await safe_goto_home(page, base_url)
    cookies_list = await page.context.cookies()
    cookies = {c["name"]: c["value"] for c in cookies_list}
    session_id = cookies.get("_vmx_saude_session", "")
    csrf = await page.evaluate(
        """() => document.querySelector('meta[name="csrf-token"]')?.content ?? ''"""
    )
    fingerprint = f"{session_id[-12:]}:{csrf[-12:] if csrf else 'no-csrf'}"
    header = await read_header_context(page)
    return SessionSnapshot(
        ts=_utc_now(),
        cookies={
            k: cookies[k]
            for k in ("_vmx_saude_session", "auth_token")
            if k in cookies
        },
        session_fingerprint=fingerprint,
        header_context=header,
    )
