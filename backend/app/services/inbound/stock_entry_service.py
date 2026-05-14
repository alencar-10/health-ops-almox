import uuid
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.inbound import InboundSession, InboundItem, InboundStatus, InboundType
from app.services.inbound.xml_parser import NFeParser

class StockEntryService:
    """
    Orchestrates the Inbound Stock Pipeline (ADR-012).
    Handles staging, reconciliation, and ledger commitment.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session_from_xml(
        self, 
        tenant_id: uuid.UUID, 
        unit_id: uuid.UUID, 
        sector_id: uuid.UUID, 
        xml_content: str
    ) -> InboundSession:
        """
        Parses an XML, creates a staging session and populates items.
        """
        # 1. Parse XML
        data = NFeParser.parse(xml_content)
        
        # 2. Create Session Header
        session = InboundSession(
            tenant_id=tenant_id,
            unit_id=unit_id,
            sector_id=sector_id,
            type=InboundType.XML_NFE,
            status=InboundStatus.STAGING,
            external_reference=data["number"],
            supplier_name=data["supplier_name"],
            raw_metadata={"series": data["series"], "issue_date": data["issue_date"]}
        )
        self.db.add(session)
        await self.db.flush() # Get session ID

        # 3. Create Items
        for item_data in data["items"]:
            # Handle multiple batches per product if present
            if not item_data["batches"]:
                # Manual entry / missing batch fallback (should be rare in NF-e)
                continue
                
            for batch in item_data["batches"]:
                # Parse expiry date
                try:
                    expiry = datetime.strptime(batch["expiry_date"], "%Y-%m-%d")
                except:
                    # Fallback or log error
                    expiry = datetime.now() # FIXME: Add proper validation

                item = InboundItem(
                    session_id=session.id,
                    raw_product_name=item_data["raw_product_name"],
                    raw_gtin=item_data["raw_gtin"],
                    batch_number=batch["batch_number"],
                    expiry_date=expiry,
                    quantity_received=batch["quantity"],
                    unit_price=item_data["unit_price"]
                )
                self.db.add(item)

        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session_details(self, session_id: uuid.UUID) -> InboundSession:
        result = await self.db.execute(
            select(InboundSession).where(InboundSession.id == session_id)
        )
        return result.scalar_one_or_none()
