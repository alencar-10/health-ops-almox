import httpx
import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class VivverClient:
    """
    HTTP Client for interacting with the Vivver ERP (Cycle 28).
    Handles authentication via cookies and multipart/form-data submissions.
    """

    def __init__(self):
        self.base_url = settings.VIVVER_URL.rstrip("/")
        self.headers = {
            "Accept": "text/html, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) HealthOps/1.0"
        }
        self.cookies = {
            "auth_token": settings.VIVVER_AUTH_TOKEN,
            "_vmx_saude_session": settings.VIVVER_SESSION_ID
        }

    async def post_form(self, endpoint: str, data: Dict[str, Any]) -> Optional[str]:
        """
        Submits a form to Vivver and returns the response body (usually HTML or JS).
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                logger.info(f"Vivver POST: {url}")
                response = client.post(
                    url,
                    data=data,
                    headers=self.headers,
                    cookies=self.cookies
                )
                
                # Check for 302 (Success usually redirects or returns 200 with JS)
                if response.status_code in [200, 302]:
                    return response.text
                else:
                    logger.error(f"Vivver Error {response.status_code}: {response.text[:500]}")
                    return None
            except Exception as e:
                logger.error(f"Vivver Connection Exception: {str(e)}")
                return None

    async def create_principle(self, payload: Dict[str, Any]) -> Optional[str]:
        """Creates an Active Ingredient in Vivver."""
        return await self.post_form("amx/principio_ativo", payload)

    async def create_product(self, payload: Dict[str, Any]) -> Optional[str]:
        """Creates a Product in Vivver."""
        return await self.post_form("amx/produto", payload)

    async def link_principle(self, payload: Dict[str, Any]) -> Optional[str]:
        """Links a Product to a Principle in Vivver."""
        return await self.post_form("amx/produto_principio_ativo", payload)
