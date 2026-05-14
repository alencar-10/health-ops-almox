from typing import Dict, Any

class VivverCatalogPayloadBuilder:
    """
    Builds payloads for Principle and Product registration in Vivver (Cycle 28).
    Derived from legacy mining (ADR-006).
    """

    @classmethod
    def build_principle(cls, name: str, form_id: str) -> Dict[str, Any]:
        """
        Payload for Active Ingredient (Princípio Ativo).
        Vivver Endpoint: amx/principio_ativo
        """
        return {
            "utf8": "✓",
            "workMode": "wmInsert",
            "amx_principio_ativo[nome]": name.upper(),
            "amx_principio_ativo[codforma]": form_id,
            "amx_principio_ativo[indativo]": "S",
            "amx_principio_ativo[indpadrao]": "N"
        }

    @classmethod
    def build_product(cls, name: str, group_id: str, subgroup_id: str, uom_id: str) -> Dict[str, Any]:
        """
        Payload for Product (Produto).
        Vivver Endpoint: amx/produto
        """
        return {
            "utf8": "✓",
            "workMode": "wmInsert",
            "amx_produto[nome]": name.upper(),
            "amx_produto[codgrupo]": group_id,
            "amx_produto[codsubgrupo]": subgroup_id,
            "amx_produto[codunidademedida]": uom_id,
            "amx_produto[indativo]": "S",
            "amx_produto[indpadrao]": "N"
        }

    @classmethod
    def build_link(cls, product_erp_id: str, principle_erp_id: str) -> Dict[str, Any]:
        """
        Payload for linking Product to Principle.
        Vivver Endpoint: amx/produto_principio_ativo
        """
        return {
            "utf8": "✓",
            "workMode": "wmInsert",
            "amx_produto_principio_ativo[codproduto]": product_erp_id,
            "amx_produto_principio_ativo[codprincipioativo]": principle_erp_id,
            "amx_produto_principio_ativo[indativo]": "S"
        }
