import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any
from decimal import Decimal

class NFeParser:
    """
    Minimal Parser for Brazilian NF-e (XML) v4.00.
    Focus on extracting items, batches, and prices for stock entry staging.
    """
    
    NAMESPACE = "{http://www.portalfiscal.inf.br/nfe}"

    @classmethod
    def parse(cls, xml_content: str) -> Dict[str, Any]:
        root = ET.fromstring(xml_content)
        
        # 1. Extract Invoice Header
        infNFe = root.find(f".//{cls.NAMESPACE}infNFe")
        if infNFe is None:
            raise ValueError("Invalid XML: infNFe not found")
            
        ide = infNFe.find(f"{cls.NAMESPACE}ide")
        emit = infNFe.find(f"{cls.NAMESPACE}emit")
        
        invoice_data = {
            "number": ide.findtext(f"{cls.NAMESPACE}nNF"),
            "series": ide.findtext(f"{cls.NAMESPACE}serie"),
            "issue_date": ide.findtext(f"{cls.NAMESPACE}dhEmi"),
            "supplier_cnpj": emit.findtext(f"{cls.NAMESPACE}CNPJ"),
            "supplier_name": emit.findtext(f"{cls.NAMESPACE}xNome"),
            "items": []
        }

        # 2. Extract Items (det)
        for det in infNFe.findall(f"{cls.NAMESPACE}det"):
            prod = det.find(f"{cls.NAMESPACE}prod")
            
            item = {
                "raw_product_name": prod.findtext(f"{cls.NAMESPACE}xProd"),
                "raw_gtin": prod.findtext(f"{cls.NAMESPACE}cEAN"),
                "quantity": Decimal(prod.findtext(f"{cls.NAMESPACE}qCom") or "0"),
                "unit_price": Decimal(prod.findtext(f"{cls.NAMESPACE}vUnCom") or "0"),
                "batches": []
            }

            # 3. Extract Batches (rastro) - NF-e 4.00 standard
            # Some XMLs might use old 'med' tag or custom tags, but 'rastro' is the standard for pharmaceuticals.
            for rastro in prod.findall(f"{cls.NAMESPACE}rastro"):
                batch = {
                    "batch_number": rastro.findtext(f"{cls.NAMESPACE}nLote"),
                    "quantity": Decimal(rastro.findtext(f"{cls.NAMESPACE}qLote") or "0"),
                    "expiry_date": rastro.findtext(f"{cls.NAMESPACE}dVal")
                }
                item["batches"].append(batch)
            
            # Fallback if no 'rastro' is found (e.g., non-pharmaceutical or old format)
            if not item["batches"]:
                # Try 'med' tag (older versions)
                med = prod.find(f"{cls.NAMESPACE}med")
                if med is not None:
                    item["batches"].append({
                        "batch_number": med.findtext(f"{cls.NAMESPACE}nLote"),
                        "quantity": item["quantity"], # Assume full quantity if not split
                        "expiry_date": med.findtext(f"{cls.NAMESPACE}dVal")
                    })

            invoice_data["items"].append(item)

        return invoice_data
