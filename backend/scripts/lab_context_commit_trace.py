"""
Fase 1 — Forense de protocolo Vivver (create_conexao).

Captura POST real, payloads, CSRF, cookies e timeline sem alterar o switcher de produção.

Usage:
  cd backend
  python -m scripts.lab_context_commit_trace --scenario legacy
  python -m scripts.lab_context_commit_trace --scenario ujs_click
  python -m scripts.lab_context_commit_trace --scenario manual --headed
  python -m scripts.lab_context_commit_trace --scenario all
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Optional

from playwright.async_api import async_playwright

# Allow running as script from backend/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.core.auth.adapters.playwright.clients.context_switcher import (
    PlaywrightContextSwitcher,
)
from app.core.auth.adapters.playwright.trace.commit_trace import (
    CommitTraceCollector,
    build_session_snapshot,
    extract_conexao_form_snapshot,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("lab_context_commit_trace")

EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "evidence" / "context-switch"
SUBMIT_BTN = "#seg_operador_conexao_btn_submit"
MUN_CONTAINER = "#s2id_seg_operador_codmunicipio"
UNIT_CONTAINER = "#s2id_seg_operador_codunidade"
SECTOR_CONTAINER = "#s2id_seg_operador_codsetor"


async def _wait_sector_lookup(page, timeout_ms: int = 15000) -> None:
    try:
        await page.wait_for_response(
            lambda r: "lookup_edit_v3" in r.url and "codsetor" in r.url,
            timeout=timeout_ms,
        )
    except Exception:
        logger.warning("Timeout aguardando lookup de setores.")


async def _login(page, base_url: str, user: str, password: str) -> None:
    await page.goto(f"{base_url}/login", timeout=90000, wait_until="domcontentloaded")
    if await page.query_selector("input#conta"):
        await page.fill("input#conta", user)
        await page.fill("input#password", password)
        await page.click("div.btn_entrar")
        await page.wait_for_selector(
            ".desktop, #desktop, .div_desktop, .menu_sistema", timeout=90000
        )
        logger.info("Login OK — desktop visível.")
    else:
        logger.info("Já autenticado ou sem tela de login.")


async def _fill_context_form(
    page,
    municipality_id: str,
    unit_id: str,
    sector_id: str,
    reselect_municipality: bool,
    collector: CommitTraceCollector,
) -> None:
    base_url = settings.VIVVER_URL.rstrip("/")
    switcher = PlaywrightContextSwitcher(page, base_url)

    await page.goto(f"{base_url}/seg/operador/conexao", timeout=60000, wait_until="domcontentloaded")
    collector._log_timeline("navigate_conexao", url=page.url)

    if reselect_municipality:
        ok = await switcher._select_in_select2(MUN_CONTAINER, municipality_id)
        collector._log_timeline("select_municipality", id=municipality_id, ok=ok)
        if not ok:
            logger.warning("Re-select município falhou; seguindo com valor pré-carregado.")

    await page.wait_for_selector(UNIT_CONTAINER, timeout=30000)

    unit_hidden = await page.input_value("#seg_operador_codunidade")
    if unit_hidden != unit_id:
        ok = await switcher._select_in_select2(UNIT_CONTAINER, unit_id)
        if not ok:
            ok = await switcher._select_in_select2(UNIT_CONTAINER, "ALMOXARIFADO")
        collector._log_timeline("select_unit", id=unit_id, ok=ok)
        unit_hidden = await page.input_value("#seg_operador_codunidade")
        if unit_hidden != unit_id:
            raise RuntimeError(f"Unidade {unit_id} não selecionada (hidden={unit_hidden}).")
    else:
        collector._log_timeline("select_unit_skipped", reason="hidden_already_set", value=unit_id)

    await page.wait_for_timeout(2000)
    await _wait_sector_lookup(page)

    sector_hidden = await page.input_value("#seg_operador_codsetor")
    if sector_hidden != sector_id:
        ok = await switcher._select_in_select2(SECTOR_CONTAINER, sector_id)
        if not ok:
            ok = await switcher._select_in_select2(SECTOR_CONTAINER, "ALMOXARIFADO")
        collector._log_timeline("select_sector", id=sector_id, ok=ok)
        sector_hidden = await page.input_value("#seg_operador_codsetor")
        if sector_hidden != sector_id:
            raise RuntimeError(f"Setor {sector_id} não selecionado (hidden={sector_hidden}).")
    else:
        collector._log_timeline("select_sector_skipped", reason="hidden_already_set", value=sector_id)


def _compute_verdict(
    summary: dict[str, Any],
    before_fp: str,
    after_fp: str,
    before_header: dict[str, str],
    after_header: dict[str, str],
) -> str:
    posts = summary.get("create_conexao_post_count", 0)
    if posts == 0:
        return "COMMIT_NOT_SENT"
    responses = summary.get("create_conexao_responses", [])
    if responses and responses[0].get("status", 0) >= 400:
        return "COMMIT_REJECTED"
    header_changed = (
        before_header.get("unidade") != after_header.get("unidade")
        or before_header.get("setor") != after_header.get("setor")
    )
    fp_changed = before_fp != after_fp
    if header_changed or fp_changed:
        return "PERSISTED"
    return "SWITCH_NOT_PERSISTED"


async def _commit_legacy(page, collector: CommitTraceCollector) -> None:
    collector._log_timeline("commit_strategy", strategy="legacy")
    await page.focus(SUBMIT_BTN)
    await page.keyboard.press("Enter")
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=10000)
    except Exception:
        pass
    if page.url.endswith("/seg/operador/conexao") or "conexao" in page.url:
        collector._log_timeline("commit_legacy_fallback", action="document.forms[0].submit()")
        await page.evaluate("document.forms[0].submit()")
        try:
            await page.wait_for_load_state("load", timeout=20000)
        except Exception:
            pass


async def _commit_ujs_click(page, collector: CommitTraceCollector) -> None:
    collector._log_timeline("commit_strategy", strategy="ujs_click")
    try:
        async with page.expect_response(
            lambda r: "create_conexao" in r.url and r.request.method == "POST",
            timeout=30000,
        ) as resp_info:
            await page.click(SUBMIT_BTN)
        response = await resp_info.value
        collector._log_timeline(
            "commit_ujs_response",
            status=response.status,
            url=response.url,
        )
    except Exception as exc:
        collector._log_timeline("commit_ujs_timeout", error=str(exc))


async def _commit_manual(page, collector: CommitTraceCollector) -> None:
    collector._log_timeline("commit_strategy", strategy="manual")
    print("\n>>> Confirme no browser (botão Confirmar). Aguardando POST create_conexao até 120s...")
    try:
        await page.wait_for_response(
            lambda r: "create_conexao" in r.url and r.request.method == "POST",
            timeout=120000,
        )
        collector._log_timeline("commit_manual_detected")
    except Exception as exc:
        collector._log_timeline("commit_manual_timeout", error=str(exc))


async def run_scenario(
    scenario: str,
    unit_id: str,
    sector_id: str,
    municipality_id: str,
    headed: bool,
    reselect_municipality: bool,
) -> Path:
    if scenario == "manual" and not headed:
        headed = True

    collector = CommitTraceCollector(scenario)
    base_url = settings.VIVVER_URL.rstrip("/")
    out_path = EVIDENCE_DIR / f"{scenario}_trace.json"
    trace_path = EVIDENCE_DIR / f"{scenario}_playwright.zip"

    if not settings.VIVVER_USER or not settings.VIVVER_PASS:
        raise SystemExit("Defina VIVVER_USER e VIVVER_PASS em backend/.env")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=not headed,
            args=["--disable-dev-shm-usage", "--no-sandbox"],
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        await context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = await context.new_page()
        collector.attach(page)

        await _login(page, base_url, settings.VIVVER_USER, settings.VIVVER_PASS)
        before_session = await build_session_snapshot(page, base_url)
        collector._log_timeline("snapshot_before_session", fingerprint=before_session.session_fingerprint)

        await _fill_context_form(
            page, municipality_id, unit_id, sector_id, reselect_municipality, collector
        )
        form_pre = await extract_conexao_form_snapshot(page)
        collector._log_timeline("form_snapshot_pre_commit")

        if scenario == "legacy":
            await _commit_legacy(page, collector)
        elif scenario == "ujs_click":
            await _commit_ujs_click(page, collector)
        elif scenario == "manual":
            await _commit_manual(page, collector)
        else:
            raise ValueError(f"Cenário desconhecido: {scenario}")

        await asyncio.sleep(1)
        try:
            form_post = await extract_conexao_form_snapshot(page)
        except Exception as exc:
            collector._log_timeline("form_snapshot_post_failed", error=str(exc))
            form_post = form_pre
        after_session = await build_session_snapshot(page, base_url)

        verdict = _compute_verdict(
            collector.summary(),
            before_session.session_fingerprint,
            after_session.session_fingerprint,
            before_session.header_context,
            after_session.header_context,
        )

        extra = {
            "scenario": scenario,
            "target": {
                "municipality_id": municipality_id,
                "unit_id": unit_id,
                "sector_id": sector_id,
            },
            "reselect_municipality": reselect_municipality,
            "commit_verdict": verdict,
            "before": {
                "session": before_session.to_dict(),
                "form": form_pre.to_dict(),
            },
            "pre_commit_form": form_pre.to_dict(),
            "post_commit_form": form_post.to_dict(),
            "after": {
                "session": after_session.to_dict(),
                "form": form_post.to_dict(),
            },
        }
        collector.save(out_path, extra=extra)
        await context.tracing.stop(path=str(trace_path))
        await browser.close()

    logger.info("Cenário %s → verdict=%s → %s", scenario, verdict, out_path)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Fase 1: trace create_conexao")
    parser.add_argument("--scenario", default="legacy", choices=["manual", "ujs_click", "legacy", "all"])
    parser.add_argument("--unit-id", default="14")
    parser.add_argument("--sector-id", default="10")
    parser.add_argument("--municipality-id", default="3128253")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--reselect-municipality", action="store_true")
    args = parser.parse_args()

    scenarios = ["manual", "ujs_click", "legacy"] if args.scenario == "all" else [args.scenario]

    async def _run_all() -> None:
        for sc in scenarios:
            headed = args.headed or sc == "manual"
            await run_scenario(
                sc,
                args.unit_id,
                args.sector_id,
                args.municipality_id,
                headed,
                args.reselect_municipality,
            )

    asyncio.run(_run_all())


if __name__ == "__main__":
    main()
