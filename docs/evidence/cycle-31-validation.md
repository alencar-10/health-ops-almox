# Evidence: Cycle 31 Validation (Platform Core Hardening)

**Data**: 2026-05-14
**Status**: SUCCESS

## 1. Login Result
- **Login Orquestrado**: OK
- **Session ID captured**: `SnlPbWx4Y3...` (masked)
- **CSRF Token captured**: `ACvqqKcEH8...` (masked)

## 2. Access Scope Discovery (XHR Interception)
A descoberta via interceptação do endpoint `lookup_edit_v3` retornou as seguintes unidades para o operador:

| ID | Nome da Unidade |
|----|-----------------|
| 5  | ACADEMIA DE SAUDE DE GUARACIAMA |
| 14 | ALMOXARIFADO DA SAUDE |
| 11 | CENTRO DE ESPECIALIDADES - UBS SANTA CLARA |
| 4  | ESF CUIDAR DE TODOS |
| 9  | EXTERNA |
| 6  | FARMACIA DE MINAS TEMPO DE CUIDAR DE TODOS |
| 12 | LABORATORIO MUNICIPAL DE GUARACIAMA |
| 7  | NASF CIDADANIA PARA TODOS |
| 8  | PSF DE GUARACIAMA |
| 2  | PSF SAUDE PARA TODOS |
| 3  | SMS DE GUARACIAMA |
| 10 | UBS SAO JOAO BATISTA PLANTOES |
| 15 | VIGILANCIA SANITARIA |

## 3. Sector Discovery
- **Unidade Testada**: ID 5 (ACADEMIA DE SAUDE)
- **Setor Encontrado**: ID 0 (ATENDIMENTO)

## 4. XHR Payload Analysis
A estrutura do payload interceptado segue o padrão:
```json
{
  "rows": [...],
  "total": 13,
  "labels": { "codunidade": "...", "nomfantasia": "..." }
}
```
Normalizado pelo sistema para o contrato `{ key, name }`.
