import asyncio
import sys
import os
import logging

# Configuração de Logs para ver o Playwright trabalhando
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RealIntegrationTest")

# Adiciona o diretório app ao path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from app.core.auth.factory import AuthEngineFactory
from app.core.session.context import OperationalContext
from app.core.config import settings

async def run_real_test():
    print("\n[REAL INTEGRATION] Iniciando Prova de Fogo (Vivver ERP)...")
    
    # 1. Verifica se temos credenciais via Settings (Secrets Provider)
    username = settings.VIVVER_USER
    password = settings.VIVVER_PASS
    
    if not username or not password:
        print("❌ ERRO: Credenciais VIVVER_USER e VIVVER_PASS não carregadas no Settings.")
        return

    # 2. Força o modo PRODUCTION para usar o Playwright
    os.environ["APP_MODE"] = "PRODUCTION"
    
    # 3. Solicita o motor real
    engine = AuthEngineFactory.get_engine()
    print(f"-> Motor ativo: {type(engine).__name__}")
    
    # 4. Executa o login real
    try:
        context = await engine.login(username, password, settings.VITE_MUNICIPALITY_ID)
        
        if context:
            print("\n[OK] INTEGRACAO REAL CONCLUIDA COM SUCESSO!")
            print(f"-> Unidade Capturada: {context.unit_name}")
            print(f"-> Setor Capturado: {context.sector_name}")
            print(f"-> Session ID: {context.session_id[:10]}...")
            print(f"-> CSRF Token: {context.csrf_token[:10]}...")
        else:
            print("[ERRO] FALHA: O motor nao conseguiu resolver o contexto real.")
            
    except Exception as e:
        print(f"[ERRO] ERRO CRITICO NA INTEGRACAO: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_real_test())
