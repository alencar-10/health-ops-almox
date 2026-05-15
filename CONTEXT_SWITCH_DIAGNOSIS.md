# Relatório de Diagnóstico: Orquestração de Contexto Vivver

> **Arquivado (pré-forense).** Resolução e causa raiz: [docs/evidence/context-switch/ROOT_CAUSE_ANALYSIS.md](docs/evidence/context-switch/ROOT_CAUSE_ANALYSIS.md).  
> Protocolo v1: [COMMIT_PROTOCOL_v1.md](docs/evidence/context-switch/COMMIT_PROTOCOL_v1.md).

**Data**: 15 de Maio de 2026  
**Status Atual**: ~~Bloqueio~~ **Resolvido** — ver documentação forense em `docs/evidence/context-switch/`  
**Objetivo**: Garantir que a troca de Unidade/Setor no HealthOps reflita instantaneamente no Vivver ERP de forma estável.

---

## 1. O que já funciona (Vitórias)
- **Login & Bootstrap**: O robô Playwright consegue realizar o login, atravessar a seleção de município e chegar ao Desktop.
- **Descoberta (Discovery)**: O sistema lista corretamente todas as unidades e setores disponíveis para o operador.
- **Mapeamento de Seletores**: Identificamos os seletores reais do Select2 (`#s2id_seg_operador_codunidade`) e os botões de confirmação (`#seg_operador_conexao_btn_submit`).
- **Sucesso Pontual**: Confirmamos via screenshot que a manobra para entrar na unidade **ALMOXARIFADO DA SAUDE (ID 14)** foi bem-sucedida.

---

## 2. Testes Realizados & Estratégias de Automação
Para tentar estabilizar a troca, as seguintes abordagens foram implementadas no `PlaywrightContextSwitcher`:

- **Estratégias de Clique**:
    - `page.click()` padrão + `dispatch_event('click')`.
    - `focus() + keyboard.press('Enter')` (simulação humana para Rails UJS).
    - `document.forms[0].submit()` via JavaScript (bypass total do botão).
- **Gestão de Espera (Waits)**:
    - Substituição de `networkidle` por `domcontentloaded` e `load` para evitar loops de polling do Vivver.
    - Implementação de buffers de hidratação pós-seleção de Unidade.
- **Resiliência**:
    - **Smart Login**: O backend não reseta mais a sessão se já estiver no Desktop.
    - **Auto-Refresh**: Força F5 e re-validação se a página travar.

---

## 3. O Ponto de Bloqueio (O "Gargalo")
O robô preenche o formulário corretamente (validado via `last_switch_error.html`), mas ao disparar a confirmação, o servidor do Vivver muitas vezes não persiste a troca ou a página entra em loop de AJAX.

---

## 4. Hipóteses para Investigação (Next Steps)
1. **Token CSRF**: Validar se o token de autenticidade do formulário está sendo enviado corretamente na requisição de troca.
2. **Dependência de Município**: Verificar se re-selecionar o município no Select2 ajuda a "destravar" a troca de unidade.
3. **Clean Slate**: Testar se fechar o browser e logar do zero resolve casos de "sessão presa".

## 5. Arquivos Chave
- `backend/app/core/auth/adapters/playwright/adapter.py`
- `backend/app/core/auth/adapters/playwright/clients/context_switcher.py`
- `backend/last_switch_error.html`
