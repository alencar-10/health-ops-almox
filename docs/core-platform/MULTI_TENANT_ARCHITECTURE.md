# Core Platform: Multi-Tenant Architecture

## 1. Modelo de Isolamento
O HealthOps opera sob um modelo de **Isolamento de Contexto**, onde a base de código é única (Plataforma), mas os dados e integrações são parametrizados pelo `TenantID`.

## 2. Tenant Resolver
O **Tenant Resolver** é o componente core que:
1.  Identifica o cliente através da URL ou identificador de login.
2.  Carrega as configurações específicas (URLs do Vivver, IDs de Município, Credenciais de Automação).
3.  Injeta estas configurações na **Auth Engine**.

## 3. Desacoplamento do ERP
Embora a implementação atual foque no Vivver, a arquitetura multi-tenant prevê que:
*   A plataforma define a **Gramática Operacional** (Entrada, Estoque, Saída).
*   Os adaptadores (Vivver, MV, Tasy) traduzem essa gramática para as APIs específicas.

## 4. Estrutura de Diretórios da Plataforma
*   `/core/auth`: Motor de autenticação (Playwright Bridge).
*   `/core/context`: Gestão de `OperationalContext`.
*   `/core/layout`: `AppShell` e UI global imutável.
*   `/modules/*`: Funcionalidades de negócio que consomem o Core.

## 5. Fluxo de Expansão
Para adicionar um novo módulo (ex: Regulação) à plataforma:
1.  O módulo deve importar o `useSession` do Core.
2.  O módulo deve usar os IDs de Unidade/Setor providos pelo Core para todas as requisições de API.
3.  O módulo deve respeitar o `AppShell` para garantir consistência visual.
