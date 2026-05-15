from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from app.core.session.context import OperationalContext

class AuthEngine(ABC):
    """
    Interface abstrata para o Motor de Autenticação da Plataforma.
    """
    
    @abstractmethod
    async def login(self, username: str, password: str, tenant_id: str) -> Optional[OperationalContext]:
        """
        Realiza o login e resolve o contexto operacional inicial.
        """
        pass

    @abstractmethod
    async def refresh(self, context: OperationalContext) -> bool:
        """
        Renova a validade da sessão operacional.
        """
        pass

    @abstractmethod
    def get_status(self) -> str:
        """
        Retorna o estado atual do motor (IDLE, LOGGING_IN, AUTHENTICATED, ERROR).
        """
        pass

class ContextDiscoveryEngine(ABC):
    """
    Interface para descoberta de escopo operacional e troca dinâmica de contexto.
    """
    
    @abstractmethod
    async def list_available_units(self) -> List[Dict]:
        """
        Lista todas as unidades disponíveis para o operador na sessão ativa.
        """
        pass

    @abstractmethod
    async def list_available_sectors(self, unit_id: str) -> List[Dict]:
        """
        Lista todos os setores disponíveis para uma unidade específica.
        """
        pass

    @abstractmethod
    async def switch_context(self, unit_id: str, sector_id: str, operation_id: Optional[str] = None) -> Optional[OperationalContext]:
        """
        Executa a troca dinâmica de contexto e revalida a integridade da sessão.
        """
        pass
