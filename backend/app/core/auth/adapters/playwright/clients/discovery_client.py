import logging
import json
from typing import List, Dict
from playwright.async_api import Page

logger = logging.getLogger(__name__)

class PlaywrightDiscoveryClient:
    """
    Responsável por mapear o escopo de acesso (Unidades/Setores) via APIs internas do ERP.
    """
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

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
            
            result = await self.page.evaluate(f"""async (url) => {{
                const response = await fetch(url, {{
                    headers: {{ 'Accept': 'application/json' }}
                }});
                return await response.json();
            }}""", full_url)

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

    async def list_sectors(self, unit_id: str) -> List[Dict]:
        """
        Lista setores disponíveis para uma unidade específica.
        """
        logger.info(f"Iniciando descoberta de setores para unidade {unit_id}...")
        
        lookup_url = f"{self.base_url}/fwk/lookup_edit_v3"
        params = {
            "model": "Seg::Operador::ConexaoQuery.search.distinct",
            "key": "codsetor",
            "name": "nomsetor", # Nome provável baseado no padrão Vivver
            "where": f",codunidade={unit_id}",
            "limit": 100
        }

        try:
            query_str = "&".join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{lookup_url}?{query_str}"
            
            result = await self.page.evaluate(f"""async (url) => {{
                const response = await fetch(url, {{
                    headers: {{ 'Accept': 'application/json' }}
                }});
                return await response.json();
            }}""", full_url)

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
