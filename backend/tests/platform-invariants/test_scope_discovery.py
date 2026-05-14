import pytest
import asyncio
import logging
from app.core.auth.adapters.playwright.adapter import PlaywrightAuthAdapter
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_real_scope_discovery():
    """
    Teste de Fogo: Valida a descoberta de escopo operacional real.
    """
    if settings.APP_MODE != "PRODUCTION":
        pytest.skip("Este teste requer APP_MODE=PRODUCTION e credenciais reais.")

    adapter = PlaywrightAuthAdapter()
    
    print("\n[DISCOVERY TEST] Iniciando Mapeamento de Território...")
    
    # 1. Login
    context = await adapter.login(
        username=settings.VIVVER_USER,
        password=settings.VIVVER_PASS,
        tenant_id="3128253"
    )
    
    assert context is not None
    print(f"-> Login OK (Sessão: {context.session_id[:10]}...)")

    # 2. Descoberta de Unidades (Stage 3)
    print("-> Solicitando catálogo de unidades via XHR Sniffing...")
    units = await adapter.list_available_units()
    
    assert isinstance(units, list)
    assert len(units) > 0
    print(f"-> SUCESSO: Descobertas {len(units)} unidades no escopo do operador.")
    assert len(units) > 0
    print(f"-> SUCESSO: Descobertas {len(units)} unidades no escopo do operador.")
    
    for u in units[:5]: # Agora units é garantidamente uma lista
        print(f"   [Unit] ID: {u.get('key')} - Nome: {u.get('name')}")

    # 3. Descoberta de Setores para a primeira unidade
    if units:
        first_unit_id = units[0].get('key')
        print(f"-> Solicitando setores para a unidade {first_unit_id}...")
        sectors = await adapter.list_available_sectors(first_unit_id)
        assert len(sectors) > 0
        print(f"-> SUCESSO: Descobertos {len(sectors)} setores para esta unidade.")
        for s in sectors[:3]:
            print(f"      [Sector] ID: {s.get('key')} - Nome: {s.get('name')}")

    print("\n[OK] TESTE DE DESCOBERTA CONCLUIDO COM SUCESSO!")

if __name__ == "__main__":
    asyncio.run(test_real_scope_discovery())
