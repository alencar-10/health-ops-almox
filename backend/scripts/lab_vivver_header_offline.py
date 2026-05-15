"""Valida read_header_context contra HTML salvo (sem rede)."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from playwright.async_api import async_playwright
from app.core.auth.adapters.playwright.trace.commit_trace import read_header_context

HTML = Path(__file__).resolve().parents[1] / "evidence" / "context-switch" / "vivver_home_after_login.html"


async def main() -> None:
    if not HTML.exists():
        raise SystemExit(f"Arquivo não encontrado: {HTML}")
    html = HTML.read_text(encoding="utf-8")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html, wait_until="domcontentloaded")
        header = await read_header_context(page)
        await browser.close()
    print(header)
    if header.get("unidade") == "N/A" or header.get("setor") == "N/A":
        raise SystemExit("FAIL: seletores #unidade_info / #setor_info não resolveram")
    print("OK — header offline")


if __name__ == "__main__":
    asyncio.run(main())
