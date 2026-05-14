import time
from typing import Dict, Any, List
from datetime import datetime
from app.models.inbound import InboundSession, InboundItem

class VivverInboundPayloadBuilder:
    """
    Builds the multipart/form-data payload for Vivver 'Entrada Direta' or 'Recebimento' (Cycle 28).
    """

    @classmethod
    def build(cls, session: InboundSession, items: List[InboundItem], operator_code: str) -> Dict[str, Any]:
        if session.type == InboundType.MANUAL:
            return cls._build_direct_entry(session, items, operator_code)
        elif session.type == InboundType.XML_NFE:
            return cls._build_supplier_receipt(session, items, operator_code)
        else:
            raise ValueError(f"Unsupported InboundType: {session.type}")

    @classmethod
    def _build_direct_entry(cls, session: InboundSession, items: List[InboundItem], operator_code: str) -> Dict[str, Any]:
        payload = {
            "oldWorkMode": "wmSearch",
            "workMode": "wmInsert",
            "utf8": "✓",
            "amx_entrada_direta_produto[codmunicipio]": "3128253",
            "amx_entrada_direta_produto[codunidade]": "10",
            "amx_entrada_direta_produto[codsetor]": "0",
            "amx_entrada_direta_produto[codoperador]": operator_code,
            "amx_entrada_direta_produto[codmotivoentr]": "9",
            "amx_entrada_direta_produto[dathoraentrada]": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "amx_entrada_direta_produto[numdocumento]": session.external_reference or "",
            "amx_entrada_direta_produto[indentradaoficialsigaf]": "N",
            "amx_entrada_direta_produto[inddatvalidade]": "N",
            "amx_entrada_direta_produto[indlote]": "N",
            "amx_entrada_direta_produto[consiste_entradas_de_produtos_sem_valor]": "N",
        }

        for i, item in enumerate(items):
            temp_key = int(time.time() * 1000) + i
            prefix = f"amx_entrada_direta_produto[item_entrada_direta_produto][{temp_key}]"
            payload.update({
                f"{prefix}[id]": "",
                f"{prefix}[codfabricante]": item.manufacturer.external_id if item.manufacturer else "",
                f"{prefix}[codproduto]": item.product.external_code if item.product else "",
                f"{prefix}[numlote]": item.batch_number,
                f"{prefix}[qdeentrada]": str(item.quantity_received),
                f"{prefix}[prcunitario]": f"{item.unit_price:.2f}".replace(".", ","),
                f"{prefix}[datvalidade]": item.expiry_date.strftime("%d/%m/%Y"),
                f"{prefix}[_destroy]": "false"
            })
        return payload

    @classmethod
    def _build_supplier_receipt(cls, session: InboundSession, items: List[InboundItem], operator_code: str) -> Dict[str, Any]:
        payload = {
            "oldWorkMode": "wmSearch",
            "workMode": "wmInsert",
            "utf8": "✓",
            "amx_recebimento_produto_fornecedor[codmunicipio]": "3128253",
            "amx_recebimento_produto_fornecedor[codunidade]": "10",
            "amx_recebimento_produto_fornecedor[codsetor]": "0",
            "amx_recebimento_produto_fornecedor[dathorarecebimento]": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "amx_recebimento_produto_fornecedor[numdocumento]": session.external_reference or "",
            "amx_recebimento_produto_fornecedor[codtipodocumento]": session.document_type or "23", # Default 23 (NF)
            "amx_recebimento_produto_fornecedor[codfornecedorexterno]": "37", # FIXME: Map from session.supplier
            "amx_recebimento_produto_fornecedor[vlrtotal]": f"{session.total_value or 0:.2f}".replace(".", ","),
            "amx_recebimento_produto_fornecedor[numcontrato]": session.contract_number or "",
            "amx_recebimento_produto_fornecedor[numrequisicao]": session.request_number or "",
            "amx_recebimento_produto_fornecedor[inddatvalidade]": "S",
            "amx_recebimento_produto_fornecedor[indlote]": "S",
            "amx_recebimento_produto_fornecedor[consiste_entradas_de_produtos_sem_valor]": "N",
        }

        for i, item in enumerate(items):
            temp_key = int(time.time() * 1000) + i
            prefix = f"amx_recebimento_produto_fornecedor[item_recebimento_produto_fornecedor][{temp_key}]"
            payload.update({
                f"{prefix}[id]": "",
                f"{prefix}[codfabricante]": item.manufacturer.external_id if item.manufacturer else "",
                f"{prefix}[codproduto]": item.product.external_code if item.product else "",
                f"{prefix}[numlote]": item.batch_number,
                f"{prefix}[qderecebida]": str(item.quantity_received),
                f"{prefix}[prcunitario]": f"{item.unit_price:.2f}".replace(".", ","),
                f"{prefix}[datvalidade]": item.expiry_date.strftime("%d/%m/%Y"),
                f"{prefix}[_destroy]": "false"
            })
        return payload
