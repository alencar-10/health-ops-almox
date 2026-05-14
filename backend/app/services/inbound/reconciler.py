import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from rapidfuzz import process, fuzz
from app.models.product import Product
from app.models.manufacturer import Manufacturer
from app.models.inbound import InboundItem, InboundSession, InboundStatus

class FuzzyReconciler:
    """
    Intelligent matching engine for stock entries.
    Matches raw XML names to existing Catalog entities.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_products(self, item: InboundItem, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Structural Matching (ADR-014):
        Composite Score = GTIN(100) | Weighted(Name, Form, Dosage)
        """
        # 1. Exact EAN Match (Gold Standard)
        if item.raw_gtin:
            gtin_result = await self.db.execute(
                select(Product).join(InboundItem, InboundItem.id == item.id)
                .join(InboundSession, InboundSession.id == InboundItem.session_id)
                .where(Product.ean == item.raw_gtin, Product.tenant_id == InboundSession.tenant_id)
            )
            exact = gtin_result.scalar_one_or_none()
            if exact:
                return [{
                    "id": exact.id, "label": exact.name, "score": 100,
                    "metadata": {"reason": "Exact EAN Match", "fields": ["ean"]}
                }]

        # 2. Fuzzy Structural Match
        result = await self.db.execute(
            select(Product).join(InboundItem, InboundItem.id == item.id)
            .join(InboundSession, InboundSession.id == InboundItem.session_id)
            .where(Product.tenant_id == InboundSession.tenant_id, Product.deleted_at == None)
        )
        products = result.scalars().all()
        if not products: return []

        matches = []
        for p in products:
            # Weighted Signal Calculation
            name_score = fuzz.WRatio(item.raw_product_name, p.name) * 0.40
            sku_score = (100 if item.raw_product_name and p.sku in item.raw_product_name else 0) * 0.20
            # TODO: Add Form/Dosage signals once catalog models are expanded
            
            total_score = name_score + sku_score
            
            matches.append({
                "id": p.id,
                "label": p.name,
                "sku": p.sku,
                "score": round(total_score, 2),
                "metadata": {"fields": ["name", "sku"]}
            })

        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:limit]

class InboundReconciler:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.fuzzy = FuzzyReconciler(db)

    async def reconcile_item(self, item_id: uuid.UUID, product_id: Optional[uuid.UUID] = None, 
                       manufacturer_id: Optional[uuid.UUID] = None, score: Optional[float] = None,
                       metadata: Optional[Dict] = None):
        result = await self.db.execute(select(InboundItem).where(InboundItem.id == item_id))
        item = result.scalar_one_or_none()
        if not item: raise ValueError("Item not found")

        # 1. Log History before change (Audit Trace - ADR-014)
        if item.product_id or item.manufacturer_id:
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "product_id": str(item.product_id),
                "manufacturer_id": str(item.manufacturer_id),
                "score": float(item.match_score) if item.match_score else None
            }
            if not item.reconciliation_history: item.reconciliation_history = []
            item.reconciliation_history.append(history_entry)

        # 2. Apply New Match
        if product_id: item.product_id = product_id
        if manufacturer_id: item.manufacturer_id = manufacturer_id
            
        item.is_matched = bool(item.product_id and item.manufacturer_id)
        item.match_score = score
        item.match_metadata = metadata
        
        # 3. Sanitary Safety Policy Engine (Hard Blocks - ADR-014)
        if item.is_matched:
            warnings = []
            is_critical = False
            
            from app.models.product import Product
            p = await self.db.get(Product, item.product_id)
            
            # CRITICAL: Form/Dosage validation (Placeholder until Catalog is expanded)
            # if p.form != item.xml_form: 
            #    warnings.append("BLOCK: Pharmaceutical Form Mismatch")
            #    is_critical = True
            
            from app.models.manufacturer import Manufacturer
            m = await self.db.get(Manufacturer, item.manufacturer_id)
            if item.raw_manufacturer_name and m and item.raw_manufacturer_name.lower() not in m.corporate_name.lower():
                warnings.append(f"Manufacturer divergence: '{item.raw_manufacturer_name}' vs '{m.corporate_name}'")
                # Manufacturers divergence is usually a WARNING, not a block
            
            if warnings:
                if not item.match_metadata: item.match_metadata = {}
                item.match_metadata["warnings"] = warnings
                item.match_metadata["is_critical"] = is_critical
                
            if is_critical:
                item.is_blocked = True
                item.is_matched = False # Cannot confirm if blocked by policy

        await self.db.commit()
        return item
    async def undo_reconciliation(self, item_id: uuid.UUID, reversed_by: str = "system", reason: str = "Human correction"):
        """
        Forensic Undo (ADR-015):
        If NOT POSTED: Simple state reset.
        If POSTED: Create Compensatory Movement (Storno) + State reset.
        """
        result = await self.db.execute(
            select(InboundItem).options(selectinload(InboundItem.session)).where(InboundItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        if not item: return

        # 1. Forensic Check (ADR-015)
        if item.session.status in [InboundStatus.POSTED, InboundStatus.ERP_SYNCED]:
            from app.services.stock.inbound_ledger_service import InboundLedgerService
            ledger = InboundLedgerService(self.db)
            await ledger.reverse_item_commitment(item_id, reversed_by, reason)
            
            # Revert session status to CONFIRMED (Drift back to operational state)
            item.session.status = InboundStatus.CONFIRMED

        # 2. Audit Trail before clearing
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "UNDO",
            "previous_product_id": str(item.product_id),
            "previous_manufacturer_id": str(item.manufacturer_id),
            "reversed_by": reversed_by,
            "reason": reason
        }
        if not item.reconciliation_history: item.reconciliation_history = []
        item.reconciliation_history.append(history_entry)

        # 3. State Reset
        item.product_id = None
        item.manufacturer_id = None
        item.is_matched = False
        item.match_score = None
        item.match_metadata = None
        item.is_blocked = False

        await self.db.commit()
        return item
