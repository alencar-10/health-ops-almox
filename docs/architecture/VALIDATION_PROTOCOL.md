# Validation Protocol: Operational Core

Protocolo obrigatório para validar mudanças na camada de plataforma e integração real com o ERP.

## 1. Testes Automatizados (Pre-flight)
- **Scope Discovery**: `backend/tests/platform-invariants/test_scope_discovery.py`
  - Valida login, XHR sniffing de unidades e setores.
- **Real Integration**: `backend/tests/platform-invariants/test_real_integration.py`
  - Valida o fluxo básico de login e resolução de contexto inicial.

## 2. Critérios de Sucesso (Checklist)
1. O login deve ocorrer em menos de 45 segundos (em produção).
2. O sistema deve capturar `_vmx_saude_session` e `csrf-token`.
3. A lista de unidades deve retornar objetos `{ key, name }`.
4. Uma troca de contexto deve resultar em um novo `csrf-token` válido.

## 3. Procedimento de Erro
Caso ocorra `TimeoutError` no Playwright:
1. Verificar se a URL base (`guaraciama-mg.vivver.com`) está acessível.
2. Validar seletores em `adapter.py` via browser assistido.
3. Verificar se o ERP disparou algum modal de aviso/bloqueio global.

## 4. Cadência de Execução
- Toda alteração em `app/core/auth`.
- Toda nova release que toque na `AuthEngine`.
- Verificação semanal de integridade de seletores.
