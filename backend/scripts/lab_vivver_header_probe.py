"""Captura HTML da home Vivver e candidatos de seletores do cabeçalho operacional."""
import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.auth.factory import AuthEngineFactory
from app.core.config import settings
from app.core.auth.adapters.playwright.trace.commit_trace import read_header_context

OUT_DIR = Path(__file__).resolve().parents[1] / "evidence" / "context-switch"
PROBE_JS = """() => {
    const hits = [];
    const keywords = /munic[ií]pio|unidade|setor|guaraciama|almoxarifado|sa[uú]de/i;
    const nodes = document.querySelectorAll(
        'span, a, div, li, td, label, strong, b, p, h1, h2, h3, .select2-chosen'
    );
    for (const el of nodes) {
        const text = (el.textContent || '').replace(/\\s+/g, ' ').trim();
        if (text.length < 3 || text.length > 120 || !keywords.test(text)) continue;
        let sel = el.id ? '#' + el.id : el.className
            ? el.tagName.toLowerCase() + '.' + [...el.classList].slice(0, 3).join('.')
            : el.tagName.toLowerCase();
        hits.push({ selector_hint: sel, text, tag: el.tagName, id: el.id || null, classes: el.className || null });
        if (hits.length >= 80) break;
    }
    const withId = [...document.querySelectorAll('[id*="unidade"],[id*="setor"],[id*="municipio"],[class*="unidade"],[class*="setor"],[class*="municipio"]')].slice(0, 40).map(el => ({
        id: el.id,
        classes: el.className,
        text: (el.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 80),
    }));
    return { keyword_hits: hits, id_class_hits: withId };
}"""


async def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    engine = AuthEngineFactory.get_engine()
    ctx = await engine.login(
        settings.VIVVER_USER,
        settings.VIVVER_PASS,
        settings.VITE_MUNICIPALITY_ID,
    )
    if not ctx:
        raise SystemExit("Login failed")

    page = engine._page
    base = engine.base_url.rstrip("/")
    await page.goto(f"{base}/", wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(1500)

    html_path = OUT_DIR / "vivver_home_after_login.html"
    html_path.write_text(await page.content(), encoding="utf-8")
    print(f"HTML salvo: {html_path}")

    header = await read_header_context(page)
    print("read_header_context:", json.dumps(header, ensure_ascii=False, indent=2))

    probe = await page.evaluate(PROBE_JS)
    probe_path = OUT_DIR / "vivver_header_probe.json"
    probe_path.write_text(json.dumps(probe, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Probe salvo: {probe_path}")

    # Pós-switch 14/10 para comparar cabeçalho
    result = await engine.switch_context(unit_id="14", sector_id="10")
    if not result:
        raise SystemExit("Switch failed")
    await page.goto(f"{base}/", wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(1500)
    header_after = await read_header_context(page)
    print("read_header_context (após switch 14/10):", json.dumps(header_after, ensure_ascii=False, indent=2))
    (OUT_DIR / "vivver_home_after_switch.html").write_text(await page.content(), encoding="utf-8")

    if not any(v != "N/A" for v in header_after.values()):
        print("WARN: cabeçalho ainda N/A — nomes vêm da Discovery no adapter.")


if __name__ == "__main__":
    asyncio.run(main())
