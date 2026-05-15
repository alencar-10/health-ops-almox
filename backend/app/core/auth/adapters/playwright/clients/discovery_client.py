import asyncio
import logging
from typing import List, Dict

from playwright.async_api import Page

logger = logging.getLogger(__name__)

_LOOKUP_EVAL_TIMEOUT_S = 20.0

class PlaywrightDiscoveryClient:
    """
    Responsável por mapear o escopo de acesso (Unidades/Setores) via APIs internas do ERP.
    """
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    async def _fetch_lookup_json(self, full_url: str) -> object:
        """Fetch lookup JSON in-page with hard timeout (evita evaluate preso no Windows)."""
        return await asyncio.wait_for(
            self.page.evaluate(
                """async (url) => {
                const controller = new AbortController();
                const timer = setTimeout(() => controller.abort(), 15000);
                try {
                    const response = await fetch(url, {
                        headers: { 'Accept': 'application/json' },
                        signal: controller.signal,
                    });
                    if (!response.ok) {
                        return { error: `HTTP ${response.status}` };
                    }
                    return await response.json();
                } finally {
                    clearTimeout(timer);
                }
            }""",
                full_url,
            ),
            timeout=_LOOKUP_EVAL_TIMEOUT_S,
        )

    async def list_units(self, municipality_id: str) -> List[Dict]:
        """
        Lista unidades disponíveis para o operador interceptando o lookup do Vivver.
        """
        logger.info(f"Iniciando descoberta de unidades para municipio {municipality_id}...")
        
        # O modelo de lookup do Vivver para unidades (extraído dos cURLs do usuário)
        lookup_url = f"{self.base_url}/fwk/lookup_edit_v3"
        params = {
            "model": "Seg::Operador::ConexaoQuery.search.distinct",
            "key": "codunidade",
            "name": "nomfantasia",
            "where": f",codmunicipio={municipality_id}",
            "limit": 100
        }

        # Executa o fetch dentro do contexto da página para herdar cookies e CSRF
        try:
            # Serializa os params para a string de query
            query_str = "&".join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{lookup_url}?{query_str}"
            
            result = await self._fetch_lookup_json(full_url)
            if isinstance(result, dict) and result.get("error"):
                raise RuntimeError(result["error"])

            # O Vivver costuma retornar um objeto com a chave 'rows' ou 'data'
            raw_units = []
            if isinstance(result, dict):
                raw_units = result.get('rows', result.get('data', []))
            elif isinstance(result, list):
                raw_units = result

            # Normaliza para o contrato da plataforma (key, name)
            units = [
                {"key": str(u.get('codunidade', u.get('key'))), "name": u.get('nomfantasia', u.get('name'))}
                for u in raw_units
            ]
            
            logger.info(f"Descobertas {len(units)} unidades.")
            return units
        except Exception as e:
            logger.error(f"Falha na descoberta de unidades: {str(e)}")
            return []

    async def list_sectors(
        self, unit_id: str, municipality_id: str = "3128253"
    ) -> List[Dict]:
        """
        Lista setores disponíveis para uma unidade específica.
        """
        logger.info(
            "Descoberta de setores: municipio=%s unidade=%s",
            municipality_id,
            unit_id,
        )

        lookup_url = f"{self.base_url}/fwk/lookup_edit_v3"
        params = {
            "model": "Seg::Operador::ConexaoQuery.search.distinct",
            "key": "codsetor",
            "name": "nomsetor",
            "where": f",codmunicipio={municipality_id},codunidade={unit_id}",
            "limit": 100,
        }

        try:
            query_str = "&".join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{lookup_url}?{query_str}"
            
            result = await self._fetch_lookup_json(full_url)
            if isinstance(result, dict) and result.get("error"):
                raise RuntimeError(result["error"])

            raw_sectors = []
            if isinstance(result, dict):
                raw_sectors = result.get('rows', result.get('data', []))
            elif isinstance(result, list):
                raw_sectors = result

            sectors = [
                {"key": str(s.get('codsetor', s.get('key'))), "name": s.get('nomsetor', s.get('name'))}
                for s in raw_sectors
            ]
            
            logger.info(f"Descobertos {len(sectors)} setores para a unidade {unit_id}.")
            return sectors
        except Exception as e:
            logger.error(f"Falha na descoberta de setores: {str(e)}")
            return []
