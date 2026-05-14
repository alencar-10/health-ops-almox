import asyncio
import sys
import os

# Adiciona o diretório app ao path para os imports funcionarem
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from app.core.auth.factory import AuthEngineFactory
from app.core.session.context import OperationalContext

async def test_platform_decoupling():
    print("\n[HARDENING TEST] Iniciando Verificação de Desacoplamento...")
    
    # 1. Solicita o motor à Factory
    engine = AuthEngineFactory.get_engine()
    print(f"-> Motor instanciado: {type(engine).__name__}")
    
    # 2. Tenta realizar o login (deve usar o MockAdapter configurado na Factory)
    context = await engine.login("qa_user", "qa_pass", "TENANT-TEST")
    
    if not context:
        print("❌ FALHA: O motor não retornou um contexto válido.")
        sys.exit(1)
        
    # 3. Valida Invariantes de Contexto
    print(f"-> Contexto Resolvido: {context.unit_name}")
    print(f"-> Operador: {context.operator_name}")
    
    assert context.unit_id == "999", "ERRO: O ID da unidade deveria ser o do Mock (999)"
    assert context.tenant_id == "TENANT-QA-001", "ERRO: O TenantID não foi resolvido corretamente"
    
    print("\n[OK] SUCESSO: O desacoplamento eh REAL. A plataforma consome o contrato e nao a implementacao.")

if __name__ == "__main__":
    asyncio.run(test_platform_decoupling())
