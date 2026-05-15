# Lessons Learned — Context Commit Protocol

**Data:** 15/05/2026  
**Audiência:** engenharia HealthOps, integração ERP, automação Playwright

---

## 1. Por que a automação visual falhou

“Visual” aqui significa: **confiar no que a tela mostra** (Select2 preenchido, botão clicado, ausência de erro visível) como prova de persistência.

O Vivver separa deliberadamente:

- **Estado de formulário** (página `/seg/operador/conexao`)
- **Estado de sessão operacional** (cookie + contexto na barra inferior da home)

A automação antiga otimizava o primeiro e **inferia** o segundo. Isso falhou porque:

1. `data-remote="true"` não navega — waits de `load` / `domcontentloaded` são irrelevantes ou enganosos
2. Submit nativo **não executa** o pipeline Rails UJS (`ajax:before`, injeção CSRF, serialização completa)
3. Fallback `forms[0].submit()` **piora** o cenário (segundo POST inválido)

**Lição:** automação visual deve servir para **chegar ao commit**, não para **validar** persistência. Validação = protocolo + fingerprint + barra ERP.

---

## 2. Por que o request legítimo importava mais que o clique

O clique em `#seg_operador_conexao_btn_submit` é apenas o gatilho humano. O que o ERP institucionaliza é o **request**:

- Método, URL, headers, body completo (incluindo `lookup_key` e `commit=Confirmar`)
- Resposta JavaScript com confirmação semântica
- Rotação de sessão

Reproduzir o clique sem garantir o request (Enter aleatório, submit nativo) gerava **falsos positivos de UI**.

**Lição:** modelar integração como **contrato HTTP/XHR**, não como sequência de gestos. Playwright deve **observar** `wait_for_response(create_conexao)`, não apenas interagir.

---

## 3. Por que coerência contextual é transacional

Contexto operacional = `(codmunicipio, codunidade, codsetor)` **atômico** no ERP.

Passos parciais são estados inválidos:

- Unidade nova com setor antigo
- Hidden atualizado sem `lookup_key` espelho
- POST enviado com setor `0` rejeitado na API antes da manobra

**Lição:** a manobra é uma **transação** com pré-condições (discovery), commit único e pós-condições (fingerprint + barra). Alinhar com [CONTEXT_COHERENCE_RULES.md](../../core-platform/CONTEXT_COHERENCE_RULES.md).

---

## 4. DOM state vs ERP persisted state

| Aspecto | DOM state | ERP persisted state |
|---------|-----------|---------------------|
| Onde | Form conexão, Select2 | Cookie + barra `#unidade_info` |
| Quando muda | A cada keystroke/lookup | Após POST 200 + sucesso |
| Confiável para auditoria | Não | Sim |
| HealthOps antes | Misturava os dois | — |
| HealthOps agora | Separa via `ConexaoCommitClient` + bar read | — |

**Lição:** nunca persistir `OperationalContext` no HealthOps só porque o modal fechou com sucesso local.

---

## 5. Armadilha semântica: IDs falsy

`sector_id="0"` é **válido** no Vivver. Tratar `0` como “ausente” em Python/JS destrói unidades inteiras (PSF) enquanto outras (Almoxarifado, setor 10) mascaram o bug.

**Lição:** validar regras de negócio contra **catálogo ERP**, não contra convenções de linguagem. Testes obrigatórios para IDs limítrofes: `0`, `"0"`, `""`.

---

## 6. Frontend não é fonte da verdade

Após switch, `GET /current` pode retornar cache/session antiga por segundos. O frontend que re-fetchava agressivamente **revertia** a UI para Almoxarifado mesmo com ERP já em PSF.

**Lição:** em PRODUCTION, soberania contextual no **backend**; frontend exibe resultado da operação e protege contra stale read (`lastSwitchRef`), não negocia commit.

---

## 7. Riscos futuros conhecidos

| Risco | Mitigação sugerida |
|-------|-------------------|
| `codoperador` muda por ambiente | Discovery dinâmico do hidden |
| Vivver altera payload (novos campos) | Lab trace em CI; versão de protocolo |
| POST duplo reintroduzido | Lint/test proibindo `form.submit()` |
| Operação sem observabilidade | Exportar `timeline` + `correlation_id` para cada switch |
| Python 3.14 + Playwright no Windows | Documentar 3.13; venv alinhado |
| `OperationStore` in-memory | Persistir operações para multi-worker |
| Retry “mágico” | Fail-closed; negociação explícita (`MULTIPLE_CHOICES`) |
| Heurística de setor automático | Manter proibição exceto `SINGLE_OPTION` |

---

## 8. O que preservar institucionalmente

1. Traces JSON por cenário (`ujs_click`, `legacy`)
2. Hipóteses **descartadas** (não apagar do histórico)
3. Protocolo v1 como contrato, não como comentário em código
4. Cenários validados reproduzíveis via `curl` + lab script

---

## Referências

- [ROOT_CAUSE_ANALYSIS.md](./ROOT_CAUSE_ANALYSIS.md)
- [ARCHITECTURAL_IMPACT.md](./ARCHITECTURAL_IMPACT.md)
- [COMMIT_PROTOCOL_v1.md](./COMMIT_PROTOCOL_v1.md)
