import logging
import asyncio
from playwright.async_api import Page

logger = logging.getLogger(__name__)

class PlaywrightContextSwitcher:
    """
    Responsável por realizar a manobra de troca de contexto no ERP.
    """
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    async def switch(self, unit_id: str, sector_id: str) -> bool:
        """
        Executa a troca de unidade e setor via interface do ERP.
        """
        logger.info(f"Iniciando manobra de troca: Unidade {unit_id}, Setor {sector_id}...")
        
        try:
            # 1. Navega para a tela de seleção de contexto (Conexão)
            # URL provável baseada na tela "Segurança - Operador"
            await self.page.goto(f"{self.base_url}/seg/operador/conexao")
            await self.page.wait_for_load_state("networkidle")

            # 2. Preenche Unidade
            # Usando seletores baseados no padrão observado em prints anteriores
            await self.page.fill("#lookup_key_seg_operador_conexao_codunidade", unit_id)
            await self.page.keyboard.press("Tab")
            await asyncio.sleep(1) # Aguarda o carregamento dos setores dependentes

            # 3. Preenche Setor
            await self.page.fill("#lookup_key_seg_operador_conexao_codsetor", sector_id)
            await self.page.keyboard.press("Enter")

            # 4. Aguarda o processamento e o redirecionamento
            await self.page.wait_for_load_state("networkidle")
            
            # 5. Verifica se houve erro (Ex: Modal de alerta ou permanência na mesma tela)
            current_url = self.page.url
            if "conexao" in current_url.lower():
                 logger.error("Troca de contexto parece ter falhado (permaneceu na tela de conexao).")
                 return False

            logger.info("Troca de contexto concluída com sucesso via UI.")
            return True

        except Exception as e:
            logger.error(f"Erro fatal na manobra de troca: {str(e)}")
            return False
