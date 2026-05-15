"""Integration smoke: login + switch to Almoxarifado 14/10."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.auth.factory import AuthEngineFactory
from app.core.config import settings


async def main() -> None:
    engine = AuthEngineFactory.get_engine()
    ctx = await engine.login(
        settings.VIVVER_USER,
        settings.VIVVER_PASS,
        settings.VITE_MUNICIPALITY_ID,
    )
    if not ctx:
        raise SystemExit("Login failed")

    print(f"Before: unit={ctx.unit_name} sector={ctx.sector_name}")
    result = await engine.switch_context(unit_id="14", sector_id="10")
    if not result:
        raise SystemExit("Switch failed")

    print(f"After: unit={result.unit_name} sector={result.sector_name}")
    print("OK — switch persisted")


if __name__ == "__main__":
    asyncio.run(main())
