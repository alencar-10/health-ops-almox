# ADR-002: Operational Context vs Session Context

## Contexto
O Almoxarifado opera em uma estrutura multi-tenancy complexa. Misturar artefatos técnicos de rede com autoridade operacional cria objetos "Frankenstein" e dificulta a evolução.

## Decisão
Separar estritamente o **OperationalContext** (Domínio) do **SessionContext** (Infraestrutura/Transporte).

- **OperationalContext**: Dados de autoridade operacional (Tenant, Unidade, Setor, Operador, Permissões).
- **SessionContext**: Artefatos técnicos de transporte e segurança (SessionID, CSRF, Cookies, AuthToken).

## Consequências
- **Desacoplamento**: Mudanças técnicas no ERP (ex: mudança de CSRF para JWT) não afetam o domínio operacional.
- **Anti-Frankenstein**: Evita que o objeto de contexto vire um híbrido de negócio e infraestrutura.
- **Prós**: Garante rastreabilidade total (Audit Trail); isolamento de dados entre unidades.
- **Contras**: Exige coordenação entre as duas camadas para manter a autoridade válida.
- **Regra**: Nenhuma movimentação de estoque pode existir sem um `OperationalContext` válido.
