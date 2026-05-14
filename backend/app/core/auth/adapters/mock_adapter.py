from typing import Optional
from app.core.auth.engine import AuthEngine
from app.core.session.context import OperationalContext

class MockAuthAdapter(AuthEngine):
    """
    Adaptador de Teste para validar o desacoplamento real da plataforma (Cycle 31).
    NÃO possui dependência de Playwright ou redes externas.
    """

    def __init__(self, base_url: str):
        self.base_url = base_url
        self._status = "IDLE"

    def get_status(self) -> str:
        return self._status

    async def login(self, username: str, password: str, tenant_id: str) -> Optional[OperationalContext]:
        self._status = "AUTHENTICATED"
        # Retornando um contexto de "QA" para provar que o sistema consome qualquer motor compatível
        return OperationalContext(
            tenant_id="TENANT-QA-001",
            prefecture_name="MUNICIPIO DE TESTE (LAB)",
            unit_id="999",
            unit_name="UNIDADE DE HOMOLOGAÇÃO QA",
            sector_id="QA-SEC",
            sector_name="SETOR DE QUALIDADE",
            operator_id="QA-USER-01",
            operator_name="Engenheiro de Hardening",
            app_mode="LAB"
        )

    async def refresh(self, context: OperationalContext) -> bool:
        return True
