# Technical Specification — OrdemFácil

**Projeto:** OrdemFácil — Sistema Web de Gerenciamento de Ordens de Serviço  
**Versão:** 1.3  
**Documento de referência:** `requirements.md`  
**Status:** Especificação técnica do MVP — Fases 1, 2 e 3 implementadas

---

## 1. Objetivo deste documento

Este documento descreve a arquitetura, os componentes, os módulos, o modelo de dados, as interfaces da API, as regras técnicas e as diretrizes de implementação do OrdemFácil.

O objetivo é orientar o desenvolvimento do MVP de forma consistente com os requisitos funcionais e não funcionais definidos em `requirements.md`.

Este documento não substitui os requisitos. Em caso de divergência, os requisitos aprovados devem ser revisados antes da implementação.

## 2. Visão técnica do produto

O OrdemFácil será uma aplicação web composta por três camadas principais:

1. **Frontend:** interface acessada pelo navegador, desenvolvida com HTML, CSS e JavaScript.
2. **Backend:** API REST desenvolvida em Python com FastAPI, responsável por autenticação, validações e regras de negócio.
3. **Banco de dados:** PostgreSQL, responsável pelo armazenamento persistente das informações.

A comunicação entre frontend e backend será realizada por HTTP, utilizando JSON. A API deverá disponibilizar documentação OpenAPI por meio dos recursos nativos do FastAPI.

### 2.1 Arquitetura lógica

```text
┌──────────────────────────────────────────────┐
│                 Navegador                    │
│          HTML + CSS + JavaScript             │
└──────────────────────┬───────────────────────┘
                       │ HTTP / JSON
                       ▼
┌──────────────────────────────────────────────┐
│                API REST                      │
│                  FastAPI                     │
│                                              │
│  Rotas → Serviços → Regras de negócio        │
│                    ↓                         │
│              Repositórios / ORM              │
└──────────────────────┬───────────────────────┘
                       │ SQL
                       ▼
┌──────────────────────────────────────────────┐
│                 PostgreSQL                   │
│                                              │
│ Usuários | Clientes | Fornecedores | OS       │
│             Histórico de OS                 │
└──────────────────────────────────────────────┘
```

### 2.2 Diretrizes arquiteturais

- Manter frontend e backend desacoplados.
- Concentrar regras de negócio no backend.
- Não confiar em validações realizadas somente no navegador.
- Organizar o backend por módulos de domínio.
- Utilizar transações nas operações que alterem múltiplas tabelas.
- Padronizar respostas e erros da API.
- Utilizar migrations para controlar a evolução do banco de dados.
- Não armazenar senhas, tokens ou segredos no código-fonte.

## 3. Premissas técnicas do MVP

Para viabilizar a primeira versão, foram fixadas as seguintes premissas (decisões registradas na Seção 19):

- O MVP será **multiempresa**: cada usuário pertence a exatamente uma empresa e todos os dados são isolados por `company_id`.
- Não haverá cadastro público de empresa no MVP; empresas e seu primeiro Administrador serão provisionados por processo administrativo controlado.
- O sistema terá os perfis Administrador, Atendente e Técnico.
- Um usuário não poderá pertencer a mais de uma empresa no MVP; o e-mail de login é único globalmente.
- Uma ordem de serviço terá um único técnico responsável, opcional na abertura.
- O número da OS será gerado por sequência atômica por empresa, nunca por contagem de registros.
- Clientes e fornecedores serão inativados, em vez de excluídos fisicamente quando houver histórico relacionado.
- A autenticação utilizará sessão server-side com cookie `HttpOnly`; não serão utilizados tokens JWT.
- A interface será responsiva, em HTML, CSS e JavaScript puro (módulos ES6), sem framework.
- O dashboard não será habilitado para o perfil Técnico no MVP.
- Anexos, geração de PDF, integrações externas e controle financeiro não fazem parte da primeira entrega.

**Importante:** o isolamento multiempresa é requisito bloqueador (Fase 2 de `tasks.md` e CA-MULTI-001 a CA-MULTI-010 de `acceptance.md`). Nenhum módulo de negócio deve ser implementado antes da fundação multiempresa estar pronta e testada.

## 4. Stack tecnológica

| Camada | Tecnologia | Uso |
|---|---|---|
| Frontend | HTML5 | Estrutura das páginas |
| Frontend | CSS3 | Estilos e responsividade |
| Frontend | JavaScript (ES Modules) | Interatividade, componentes reutilizáveis e consumo da API |
| Backend | Python | Linguagem principal |
| Backend | FastAPI | API REST |
| Persistência | PostgreSQL | Banco de dados relacional |
| ORM | SQLAlchemy | Mapeamento objeto-relacional |
| Migrations | Alembic | Versionamento do esquema do banco |
| Validação | Pydantic | Validação de entrada e saída |
| Servidor ASGI | Uvicorn | Execução da aplicação FastAPI |
| Testes | Pytest | Testes automatizados do backend |

As versões das dependências deverão ser fixadas em arquivo de dependências e atualizadas de forma controlada.

## 5. Organização do projeto

Estrutura adotada para o repositório:

```text
ordemfacil/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── permissions.py
│   │   ├── database/
│   │   │   ├── session.py
│   │   │   └── base.py
│   │   ├── models/
│   │   │   ├── company.py
│   │   │   ├── user.py
│   │   │   ├── customer.py
│   │   │   ├── supplier.py
│   │   │   ├── service_order.py
│   │   │   ├── service_order_history.py
│   │   │   └── service_order_sequence.py
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   ├── company.py
│   │   │   ├── user.py
│   │   │   ├── customer.py
│   │   │   ├── supplier.py
│   │   │   ├── service_order.py
│   │   │   └── dashboard.py
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── customers.py
│   │   │   ├── suppliers.py
│   │   │   ├── service_orders.py
│   │   │   └── dashboard.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── user_service.py
│   │   │   ├── customer_service.py
│   │   │   ├── supplier_service.py
│   │   │   ├── service_order_service.py
│   │   │   └── dashboard_service.py
│   │   └── repositories/
│   │       ├── customer_repository.py
│   │       ├── supplier_repository.py
│   │       └── service_order_repository.py
│   │
│   ├── alembic/
│   │   └── versions/
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── index.html
│   ├── assets/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── pages/
│   └── components/
│
├── docs/                       # documentação complementar
│
├── requirements.md             # documentação principal na raiz
├── spec.md
├── design.md
├── tasks.md
├── acceptance.md
├── AGENTS.md
├── README.md
└── .gitignore
```

A estrutura poderá ser ajustada durante a implementação, desde que a separação de responsabilidades seja preservada.

## 6. Módulos do sistema

### 6.1 Autenticação e usuários

Responsável por autenticar usuários e controlar permissões.

**Responsabilidades:**
- Login e logout.
- Identificação do usuário autenticado.
- Gerenciamento de usuários pelo administrador.
- Associação de perfil ao usuário.
- Bloqueio de usuários inativos.
- Proteção de rotas e operações.

**Perfis:**

| Perfil | Permissões gerais |
|---|---|
| Administrador | Acesso completo e gerenciamento de usuários |
| Atendente | Clientes, fornecedores e gerenciamento operacional de OS |
| Técnico | Consulta e atualização das OS atribuídas |

O backend deverá verificar o perfil e a relação do técnico com a OS em cada operação protegida.

### 6.2 Clientes

Responsável pelo cadastro e gerenciamento dos clientes.

**Operações:**
- Criar cliente.
- Listar e pesquisar clientes.
- Consultar detalhes.
- Atualizar cadastro.
- Inativar cadastro.

**Validações:**
- Nome ou razão social obrigatório.
- Tipo de pessoa obrigatório: física ou jurídica.
- CPF/CNPJ, quando informado, deverá ser validado e normalizado.
- E-mail deverá respeitar formato válido, quando informado.
- Telefone deverá aceitar formatação nacional.
- Não permitir duplicidade de CPF/CNPJ entre cadastros ativos, quando o documento for informado.

### 6.3 Fornecedores

Responsável pelo cadastro e consulta de fornecedores.

**Operações:**
- Criar fornecedor.
- Listar e pesquisar fornecedores.
- Consultar detalhes.
- Atualizar cadastro.
- Inativar cadastro.

O cadastro deverá aceitar nome ou razão social, documento quando aplicável, contato, telefone, e-mail, endereço e observações.

### 6.4 Ordens de serviço

Módulo central do sistema.

**Operações:**
- Abrir ordem de serviço.
- Gerar número único.
- Vincular cliente.
- Atribuir técnico.
- Consultar e filtrar ordens.
- Editar informações permitidas.
- Atualizar status.
- Registrar observações técnicas.
- Registrar solução aplicada.
- Cancelar ordem com justificativa.
- Consultar histórico.

**Dados principais da OS:**
- Identificador interno.
- Número público da OS.
- Cliente.
- Técnico responsável.
- Descrição da solicitação.
- Serviço solicitado.
- Observações.
- Status.
- Data/hora de abertura.
- Data/hora de conclusão, quando aplicável.
- Solução aplicada, quando concluída.
- Usuário que abriu a ordem.

### 6.5 Dashboard

O dashboard deverá apresentar, no mínimo:

- Total de ordens abertas.
- Total de ordens em andamento.
- Total de ordens aguardando.
- Total de ordens concluídas.
- Total de ordens canceladas.
- Ordens abertas recentemente.

Os indicadores deverão ser calculados a partir dos dados persistidos no banco. Os números exibidos deverão respeitar o escopo de acesso do usuário.

## 7. Modelo de dados inicial

O modelo abaixo representa a estrutura lógica do MVP. **Todas as tabelas de negócio possuem `company_id`** para garantir o isolamento multiempresa. Tipos e restrições definitivos deverão ser implementados nas migrations.

### 7.1 Entidade `companies`

| Campo | Tipo sugerido | Regras |
|---|---|---|
| id | UUID | Chave primária |
| legal_name | VARCHAR(180) | Obrigatório (razão social ou nome do titular) |
| trade_name | VARCHAR(180) | Opcional (nome fantasia) |
| document | VARCHAR(20) | Opcional; normalizado |
| email | VARCHAR(255) | Opcional |
| phone | VARCHAR(30) | Opcional |
| is_active | BOOLEAN | Padrão verdadeiro |
| created_at | TIMESTAMP | Data de criação |
| updated_at | TIMESTAMP | Última atualização |

### 7.2 Entidade `users`

| Campo | Tipo sugerido | Regras |
|---|---|---|
| id | UUID | Chave primária |
| company_id | UUID | FK para `companies`; obrigatório |
| name | VARCHAR(150) | Obrigatório |
| email | VARCHAR(255) | Obrigatório e único globalmente |
| password_hash | VARCHAR(255) | Obrigatório |
| role | VARCHAR(30) | ADMIN, ATTENDANT ou TECHNICIAN |
| is_active | BOOLEAN | Padrão verdadeiro |
| created_at | TIMESTAMP | Data de criação |
| updated_at | TIMESTAMP | Última atualização |

Um usuário pertence a uma única empresa no MVP. A unicidade global do e-mail é uma limitação documentada (Seção 19).

### 7.3 Entidade `customers`

| Campo | Tipo sugerido | Regras |
|---|---|---|
| id | UUID | Chave primária |
| company_id | UUID | FK para `companies`; obrigatório |
| person_type | VARCHAR(2) | PF ou PJ |
| name | VARCHAR(180) | Obrigatório |
| document | VARCHAR(20) | Opcional; normalizado |
| phone | VARCHAR(30) | Opcional |
| email | VARCHAR(255) | Opcional |
| postal_code | VARCHAR(10) | Opcional |
| street | VARCHAR(180) | Opcional |
| number | VARCHAR(20) | Opcional |
| complement | VARCHAR(100) | Opcional |
| neighborhood | VARCHAR(100) | Opcional |
| city | VARCHAR(100) | Opcional |
| state | CHAR(2) | Opcional |
| notes | TEXT | Opcional |
| is_active | BOOLEAN | Padrão verdadeiro |
| created_at | TIMESTAMP | Data de criação |
| updated_at | TIMESTAMP | Última atualização |

### 7.4 Entidade `suppliers`

| Campo | Tipo sugerido | Regras |
|---|---|---|
| id | UUID | Chave primária |
| company_id | UUID | FK para `companies`; obrigatório |
| name | VARCHAR(180) | Obrigatório |
| document | VARCHAR(20) | Opcional |
| contact_name | VARCHAR(150) | Opcional |
| phone | VARCHAR(30) | Opcional |
| email | VARCHAR(255) | Opcional |
| address | TEXT | Opcional |
| notes | TEXT | Opcional |
| is_active | BOOLEAN | Padrão verdadeiro |
| created_at | TIMESTAMP | Data de criação |
| updated_at | TIMESTAMP | Última atualização |

### 7.5 Entidade `service_orders`

| Campo | Tipo sugerido | Regras |
|---|---|---|
| id | UUID | Chave primária |
| company_id | UUID | FK para `companies`; obrigatório |
| order_number | BIGINT | Obrigatório; único por empresa (`UNIQUE (company_id, order_number)`) |
| customer_id | UUID | FK para `customers` da mesma empresa |
| technician_id | UUID | FK para `users` da mesma empresa com perfil TECHNICIAN; opcional na abertura |
| opened_by_id | UUID | FK para `users` da mesma empresa |
| title | VARCHAR(180) | Obrigatório |
| description | TEXT | Obrigatório |
| requested_service | TEXT | Opcional |
| status | VARCHAR(30) | Status controlado |
| notes | TEXT | Opcional |
| resolution | TEXT | Obrigatória para concluir |
| cancellation_reason | TEXT | Obrigatória para cancelar |
| opened_at | TIMESTAMP | Gerada pelo servidor |
| completed_at | TIMESTAMP | Preenchida ao concluir |
| created_at | TIMESTAMP | Data de criação |
| updated_at | TIMESTAMP | Última atualização |

O número da OS é gerado por `service_order_sequences` (Seção 7.7), de forma atômica e transacional. Não deve ser calculado contando registros existentes. Cada empresa inicia sua sequência em 1.

### 7.6 Entidade `service_order_history`

| Campo | Tipo sugerido | Regras |
|---|---|---|
| id | UUID | Chave primária |
| company_id | UUID | FK para `companies`; obrigatório e igual ao da OS |
| service_order_id | UUID | FK para `service_orders` da mesma empresa |
| user_id | UUID | FK para `users` da mesma empresa |
| event_type | VARCHAR(40) | Tipo do evento |
| old_status | VARCHAR(30) | Opcional |
| new_status | VARCHAR(30) | Opcional |
| description | TEXT | Descrição do evento |
| created_at | TIMESTAMP | Data/hora gerada pelo servidor |

O histórico deverá registrar, no mínimo, abertura, alteração de status, atribuição ou troca de técnico, observações relevantes, conclusão e cancelamento.

### 7.7 Entidade `service_order_sequences`

| Campo | Tipo sugerido | Regras |
|---|---|---|
| company_id | UUID | Chave primária e FK para `companies` |
| next_value | BIGINT | Próximo número a ser atribuído; padrão 1 |
| updated_at | TIMESTAMP | Última atualização |

A geração do número da OS deve usar atualização atômica (por exemplo, `UPDATE ... RETURNING`) dentro da mesma transação de abertura da ordem, garantindo unicidade mesmo com criações concorrentes.

### 7.8 Entidade `user_sessions`

| Campo | Tipo sugerido | Regras |
|---|---|---|
| id | UUID | Chave primária |
| user_id | UUID | FK para `users`; obrigatório; exclusão em cascata |
| token_hash | VARCHAR(64) | Hash SHA-256 do identificador opaco; obrigatório e único |
| csrf_token_hash | VARCHAR(64) | Hash SHA-256 do token CSRF da sessão; obrigatório |
| expires_at | TIMESTAMP | Expiração calculada pelo servidor a partir de `SESSION_EXPIRE_MINUTES` |
| revoked_at | TIMESTAMP | Preenchido no logout; nulo enquanto a sessão está ativa |
| created_at | TIMESTAMP | Data de criação |
| updated_at | TIMESTAMP | Última atualização |

O identificador da sessão e o token CSRF existem em texto puro apenas no cookie/enviados pelo cliente; o banco armazena somente seus hashes. A sessão é considerada válida quando não revogada, não expirada e o usuário/empresa estão ativos.

### 7.9 Relacionamentos

- `companies` 1:N `users`.
- `companies` 1:N `customers`.
- `companies` 1:N `suppliers`.
- `companies` 1:N `service_orders`.
- `companies` 1:N `service_order_history`.
- `companies` 1:1 `service_order_sequences`.
- `customers` 1:N `service_orders`.
- `users` 1:N `service_orders` como responsável pela abertura.
- `users` 1:N `service_orders` como técnico responsável.
- `service_orders` 1:N `service_order_history`.
- `users` 1:N `service_order_history`.
- `users` 1:N `user_sessions`.

Fornecedores serão cadastrados de forma independente no MVP. Um vínculo entre fornecedor e OS poderá ser acrescentado futuramente, caso o fluxo de trabalho exija registrar peças ou serviços terceirizados.

## 8. Estados e transições da ordem de serviço

### 8.1 Estados

| Código | Rótulo | Significado |
|---|---|---|
| OPEN | Aberta | OS registrada e aguardando atendimento |
| IN_PROGRESS | Em andamento | Serviço em execução |
| WAITING | Aguardando | Serviço pendente de peça, informação ou autorização |
| COMPLETED | Concluída | Serviço finalizado |
| CANCELED | Cancelada | Ordem encerrada sem continuidade |

### 8.2 Transições iniciais propostas

```text
                 ┌──────────────┐
                 │    Aberta    │
                 └──────┬───────┘
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
       ┌─────────────┐      ┌─────────────┐
       │ Em andamento│◄────►│  Aguardando │
       └──────┬──────┘      └─────────────┘
              │
              ▼
       ┌─────────────┐
       │  Concluída  │
       └─────────────┘

       Aberta, Em andamento ou Aguardando
                       │
                       ▼
                ┌─────────────┐
                │  Cancelada  │
                └─────────────┘
```

Regras propostas:
- Uma OS deverá iniciar em `OPEN`.
- `OPEN` poderá avançar para `IN_PROGRESS` ou `CANCELED`.
- `IN_PROGRESS` poderá avançar para `WAITING`, `COMPLETED` ou `CANCELED`.
- `WAITING` poderá retornar para `IN_PROGRESS` ou avançar para `CANCELED`.
- `COMPLETED` e `CANCELED` serão estados finais no MVP.
- Reabertura de OS concluída ou cancelada não será permitida inicialmente.
- A conclusão exigirá o preenchimento de `resolution`.
- O cancelamento exigirá `cancellation_reason`.

As transições deverão ser validadas no serviço de domínio, nunca apenas na interface. As permissões por perfil para cada transição estão definidas na Seção 9.9.

## 9. API REST

A API deverá utilizar prefixo `/api/v1`.

### 9.1 Padrões gerais

- Formato de dados: JSON.
- Identificadores: UUID.
- Datas: ISO 8601, armazenadas preferencialmente em UTC.
- Paginação nas listagens.
- Filtros por parâmetros de consulta.
- Respostas de erro padronizadas.
- Autenticação por sessão server-side em cookie `HttpOnly`, com token CSRF.
- Documentação OpenAPI disponibilizada pelo FastAPI em ambiente de desenvolvimento.

### 9.2 Autenticação

| Método | Endpoint | Descrição | Acesso |
|---|---|---|---|
| POST | `/api/v1/auth/login` | Autenticar e criar sessão | Público |
| POST | `/api/v1/auth/logout` | Encerrar sessão e revogar cookie | Autenticado |
| GET | `/api/v1/auth/me` | Consultar usuário autenticado e sua empresa | Autenticado |

**Decisão do MVP:** autenticação por sessão server-side com identificador opaco armazenado como hash no banco e enviado ao navegador em cookie `HttpOnly`, `Secure` em produção e `SameSite=Lax`. Não serão utilizados tokens JWT. Requisições que alteram estado (`POST`, `PUT`, `PATCH`, `DELETE`) deverão enviar token CSRF válido. A sessão expira conforme `SESSION_EXPIRE_MINUTES` e é revogada no logout.

**Validação CSRF:** o cookie `CSRF_COOKIE_NAME` é legível pelo frontend, que deve ecoá-lo no cabeçalho `X-CSRF-Token`. O backend exige que cookie e cabeçalho sejam iguais e que o hash do token corresponda ao registrado na sessão autenticada. `POST /auth/login` é a única exceção: é uma operação pública, executada antes de existir sessão autenticada, e responde emitindo ambos os cookies. Limitação de tentativas de login é aplicada por credencial informada e origem da requisição (`LOGIN_MAX_ATTEMPTS`, `LOGIN_LOCKOUT_MINUTES`), com resposta HTTP 429 quando excedida.

### 9.3 Usuários

| Método | Endpoint | Descrição | Acesso |
|---|---|---|---|
| GET | `/api/v1/users` | Listar usuários | Administrador |
| POST | `/api/v1/users` | Criar usuário | Administrador |
| GET | `/api/v1/users/{id}` | Consultar usuário | Administrador |
| PUT | `/api/v1/users/{id}` | Atualizar usuário | Administrador |
| PATCH | `/api/v1/users/{id}/status` | Ativar ou inativar usuário | Administrador |

### 9.4 Clientes

| Método | Endpoint | Descrição | Acesso |
|---|---|---|---|
| GET | `/api/v1/customers` | Listar e pesquisar clientes | Administrador, Atendente |
| POST | `/api/v1/customers` | Cadastrar cliente | Administrador, Atendente |
| GET | `/api/v1/customers/{id}` | Consultar cliente | Administrador, Atendente |
| PUT | `/api/v1/customers/{id}` | Atualizar cliente | Administrador, Atendente |
| PATCH | `/api/v1/customers/{id}/status` | Inativar ou reativar cliente | Administrador |

### 9.5 Fornecedores

| Método | Endpoint | Descrição | Acesso |
|---|---|---|---|
| GET | `/api/v1/suppliers` | Listar e pesquisar fornecedores | Administrador, Atendente |
| POST | `/api/v1/suppliers` | Cadastrar fornecedor | Administrador |
| GET | `/api/v1/suppliers/{id}` | Consultar fornecedor | Administrador, Atendente |
| PUT | `/api/v1/suppliers/{id}` | Atualizar fornecedor | Administrador |
| PATCH | `/api/v1/suppliers/{id}/status` | Inativar ou reativar fornecedor | Administrador |

### 9.6 Ordens de serviço

| Método | Endpoint | Descrição | Acesso |
|---|---|---|---|
| GET | `/api/v1/service-orders` | Listar, pesquisar e filtrar OS | Administrador e Atendente (todas da empresa); Técnico (somente atribuídas) |
| POST | `/api/v1/service-orders` | Abrir OS | Administrador, Atendente |
| GET | `/api/v1/service-orders/{id}` | Consultar detalhes da OS | Administrador e Atendente (todas da empresa); Técnico (somente atribuídas) |
| PUT | `/api/v1/service-orders/{id}` | Atualizar campos operacionais permitidos | Administrador, Atendente |
| PATCH | `/api/v1/service-orders/{id}/technician` | Atribuir ou trocar técnico | Administrador, Atendente |
| PATCH | `/api/v1/service-orders/{id}/status` | Atualizar status | Administrador, Atendente e Técnico atribuído, conforme Seção 9.9 |
| POST | `/api/v1/service-orders/{id}/notes` | Registrar observação técnica | Administrador e Técnico atribuído |
| POST | `/api/v1/service-orders/{id}/complete` | Concluir OS e registrar solução | Administrador e Técnico atribuído |
| POST | `/api/v1/service-orders/{id}/cancel` | Cancelar OS com justificativa | Administrador |

Para técnicos, as operações de consulta e atualização deverão verificar se a OS está atribuída ao usuário autenticado. A matriz completa de permissões está na Seção 9.9.

### 9.7 Dashboard

| Método | Endpoint | Descrição | Acesso |
|---|---|---|---|
| GET | `/api/v1/dashboard/summary` | Indicadores gerais por status | Administrador, Atendente |
| GET | `/api/v1/dashboard/recent-orders` | Ordens recentes | Administrador, Atendente |

O dashboard não é habilitado para o perfil Técnico no MVP; a tela inicial do técnico é a listagem das OS atribuídas a ele.

### 9.8 Filtros e paginação de OS

O endpoint de listagem deverá aceitar parâmetros semelhantes a:

```http
GET /api/v1/service-orders?page=1&page_size=20&status=OPEN&customer_id={uuid}&start_date=2026-01-01&end_date=2026-01-31&search=123
```

Parâmetros previstos:
- `page`: página solicitada.
- `page_size`: quantidade por página, com limite máximo definido.
- `status`: status da ordem.
- `customer_id`: identificador do cliente.
- `technician_id`: identificador do técnico, para perfis autorizados.
- `start_date` e `end_date`: intervalo de abertura.
- `search`: busca por número da OS ou nome do cliente.

A API deverá validar os filtros e impedir que um técnico consulte ordens de outros técnicos apenas alterando parâmetros da URL.

### 9.9 Matriz de permissões do MVP

| Operação | Administrador | Atendente | Técnico |
|---|---|---|---|
| Usuários | Criar, consultar, editar, ativar e inativar | — | — |
| Minha Empresa | Consultar e editar | — | — |
| Clientes — criar, editar e consultar | Sim | Sim | — |
| Clientes — inativar e reativar | Sim | — | — |
| Fornecedores — consultar | Sim | Sim | — |
| Fornecedores — criar, editar e inativar | Sim | — | — |
| Dashboard | Sim | Sim | Não habilitado |
| Abrir OS | Sim | Sim | — |
| Listar e consultar OS | Todas da empresa | Todas da empresa | Somente atribuídas |
| Editar campos operacionais da OS | Sim | Sim | — |
| Atribuir ou trocar técnico | Sim | Sim | — |
| Registrar observação técnica | Sim | — | Somente em OS atribuída |
| Registrar solução e concluir | Sim | — | Somente em OS atribuída |
| Cancelar OS | Sim | — | — |
| Consultar histórico da OS | Sim | Sim | Somente em OS atribuída |

Transições de status por perfil:

| Transição | Administrador | Atendente | Técnico atribuído |
|---|---|---|---|
| `OPEN` → `IN_PROGRESS` | Sim | Sim | Sim |
| `IN_PROGRESS` → `WAITING` | Sim | Sim | Sim |
| `WAITING` → `IN_PROGRESS` | Sim | Sim | Sim |
| `IN_PROGRESS` → `COMPLETED` | Sim | — | Sim (exige `resolution`) |
| `OPEN` / `IN_PROGRESS` / `WAITING` → `CANCELED` | Sim | — | — (exige `cancellation_reason`) |

O técnico não edita os dados gerais da solicitação, não atribui técnico e não cancela OS. Conclusão e cancelamento exigem confirmação na interface e registro obrigatório no histórico.

## 10. Padrão de resposta da API

### 10.1 Resposta de sucesso

Os endpoints deverão retornar os códigos HTTP apropriados e os dados previstos para cada operação.

Exemplo ilustrativo:

```json
{
  "id": "uuid",
  "order_number": 1001,
  "status": "OPEN",
  "message": "Ordem de serviço criada com sucesso."
}
```

### 10.2 Resposta de erro

Formato sugerido:

```json
{
  "detail": {
    "code": "VALIDATION_ERROR",
    "message": "Não foi possível concluir a operação.",
    "fields": {
      "customer_id": "Cliente não encontrado."
    }
  }
}
```

Códigos HTTP principais:
- `200 OK`: consulta ou atualização concluída.
- `201 Created`: registro criado.
- `204 No Content`: operação concluída sem corpo de resposta.
- `400 Bad Request`: solicitação inválida ou transição não permitida.
- `401 Unauthorized`: usuário não autenticado.
- `403 Forbidden`: usuário sem permissão.
- `404 Not Found`: recurso não encontrado.
- `409 Conflict`: conflito, como documento duplicado.
- `422 Unprocessable Entity`: dados não passaram na validação.
- `500 Internal Server Error`: erro inesperado.

Mensagens destinadas ao usuário não deverão expor detalhes internos, SQL, caminhos locais, tokens ou stack traces.

## 11. Segurança

A implementação deverá observar, no mínimo, as seguintes diretrizes:

1. Armazenar senhas somente como hash, utilizando algoritmo apropriado para senhas, como Argon2id ou bcrypt com configuração segura.
2. Utilizar HTTPS em produção.
3. Proteger endpoints privados por autenticação.
4. Validar permissões no backend em todas as operações protegidas.
5. Aplicar validação de entrada com Pydantic e restrições no banco.
6. Configurar CORS somente para as origens autorizadas.
7. Manter segredos em variáveis de ambiente ou serviço de gerenciamento de segredos.
8. Não registrar senhas, tokens ou dados pessoais desnecessários nos logs.
9. Aplicar limitação de tentativas de login e medidas contra abuso.
10. Utilizar consultas parametrizadas ou ORM para reduzir risco de SQL injection.
11. Restringir o acesso de técnicos às OS atribuídas.
12. Registrar eventos importantes para auditoria.
13. Manter dependências atualizadas e revisar vulnerabilidades.
14. Definir política de backup e teste de restauração.
15. Armazenar identificadores de sessão somente como hash no banco e revogá-los no logout.
16. Exigir token CSRF nas requisições que alteram estado quando a autenticação utilize cookie.

### 11.1 LGPD e dados pessoais

O sistema armazenará dados pessoais de clientes, fornecedores e usuários. A implementação deverá:
- Coletar somente dados necessários à operação.
- Restringir o acesso conforme a função do usuário.
- Definir finalidade e política de retenção dos dados.
- Proteger dados em trânsito e em repouso conforme a infraestrutura disponível.
- Permitir atendimento a solicitações de titulares, conforme os procedimentos definidos pela empresa.
- Evitar exposição de documentos pessoais em listagens e logs.

As responsabilidades legais, bases legais e prazos de retenção deverão ser definidos pelo controlador dos dados com orientação apropriada. Este documento não constitui parecer jurídico.

## 12. Interface e experiência do usuário

A interface deverá priorizar clareza, facilidade de navegação e rapidez na localização de informações.

### 12.1 Estrutura inicial de telas

- Login.
- Dashboard.
- Listagem de ordens de serviço.
- Abertura de ordem de serviço.
- Detalhes da ordem de serviço.
- Edição da ordem de serviço.
- Listagem e formulário de clientes.
- Listagem e formulário de fornecedores.
- Gerenciamento de usuários.
- Perfil e configurações básicas.

### 12.2 Diretrizes de interface

- Menu de navegação consistente.
- Formulários com rótulos claros e indicação de campos obrigatórios.
- Mensagens de sucesso, erro e confirmação.
- Confirmação antes de cancelar uma OS ou executar ações sensíveis.
- Filtros visíveis na listagem de OS.
- Status identificados por texto e elemento visual, sem depender somente de cores.
- Paginação nas listagens.
- Layout adaptável a telas pequenas.
- Estados de carregamento e telas vazias.
- Acessibilidade básica: navegação por teclado, contraste adequado e rótulos associados aos campos.

O detalhamento visual, componentes e protótipos deverão ser registrados em `design.md`.

## 13. Requisitos de desempenho e escalabilidade

Para o MVP:
- Utilizar paginação em listagens.
- Criar índices para campos consultados frequentemente, como `order_number`, `status`, `customer_id`, `technician_id` e `opened_at`.
- Evitar consultas repetidas desnecessárias.
- Retornar somente os campos necessários em cada listagem.
- Definir limites de tamanho para paginação e campos textuais.
- Monitorar tempo de resposta e erros em produção.

Metas numéricas de desempenho deverão ser definidas após estimar quantidade de usuários, volume de ordens e infraestrutura de hospedagem.

## 14. Logs, auditoria e tratamento de erros

- Registrar erros técnicos no backend sem expor informações sensíveis.
- Associar eventos de negócio ao usuário autenticado.
- Registrar data e hora pelo servidor.
- Manter histórico de alterações de status.
- Registrar atribuição e troca de técnico.
- Registrar conclusão e cancelamento.
- Não permitir que usuários comuns alterem ou apaguem o histórico.
- Definir política de retenção dos logs técnicos.

O histórico da OS é um registro de negócio e deverá permanecer associado à ordem mesmo após sua conclusão ou cancelamento.

## 15. Ambiente e configuração

### 15.1 Variáveis de ambiente

Exemplo de configuração, sem valores reais:

```env
APP_NAME=OrdemFacil
APP_ENV=development
APP_DEBUG=true
API_V1_PREFIX=/api/v1

DATABASE_URL=postgresql+psycopg://usuario:senha@localhost:5432/ordemfacil

SECRET_KEY=definir-uma-chave-longa-e-aleatoria
SESSION_EXPIRE_MINUTES=480
SESSION_COOKIE_NAME=ordemfacil_session
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_SAMESITE=lax
CSRF_COOKIE_NAME=ordemfacil_csrf
LOGIN_MAX_ATTEMPTS=5
LOGIN_LOCKOUT_MINUTES=15

CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
```

Regras:
- O arquivo `.env` não deverá ser versionado; o modelo fica em `backend/.env.example`.
- O arquivo `.env.example` deverá conter somente nomes e exemplos fictícios.
- Produção deverá utilizar `APP_DEBUG=false` e `SESSION_COOKIE_SECURE=true`.
- A chave secreta deverá ser forte e exclusiva por ambiente.
- As origens CORS deverão ser configuradas conforme o domínio real do frontend.
- Identificadores de sessão devem ser armazenados como hash e tokens CSRF validados nas operações de escrita.

### 15.2 Ambientes

- **Desenvolvimento:** execução local para implementação.
- **Teste:** ambiente para validação integrada.
- **Produção:** ambiente publicado e acessível aos usuários.

As configurações e credenciais deverão ser separadas por ambiente.

## 16. Testes

A implementação deverá incluir testes automatizados e validações manuais.

### 16.1 Testes unitários

- Validação de CPF/CNPJ, quando aplicável.
- Regras de transição de status.
- Regras de conclusão e cancelamento.
- Verificação de permissões.
- Geração de número de OS.

### 16.2 Testes de integração

- Login e acesso a rotas protegidas.
- Criação, consulta e atualização de clientes.
- Criação e consulta de fornecedores.
- Abertura de OS e geração do número.
- Atribuição de técnico.
- Atualização de status.
- Registro de histórico.
- Filtros e paginação.
- Bloqueio de acesso indevido.

### 16.3 Testes de interface

- Navegação entre telas.
- Validação dos formulários.
- Exibição de mensagens de erro e sucesso.
- Pesquisa e filtros.
- Responsividade em computador e celular.
- Acessibilidade básica.

## 17. Implantação e operação

A aplicação deverá ser preparada para implantação em servidor com acesso à internet.

Diretrizes:
- Executar FastAPI por servidor ASGI adequado.
- Utilizar PostgreSQL como serviço de banco de dados.
- Utilizar proxy reverso e HTTPS em produção.
- Executar migrations de forma controlada.
- Configurar backup periódico do banco.
- Manter logs e monitoramento básico.
- Não utilizar servidor de desenvolvimento em produção.

Docker e Docker Compose poderão ser adotados para padronizar o ambiente de desenvolvimento e implantação, mas a decisão final de hospedagem será documentada posteriormente.

## 18. Critérios técnicos de conclusão

A implementação técnica do MVP será considerada concluída quando:

- A aplicação frontend conseguir consumir a API.
- O backend estiver organizado em módulos e com documentação OpenAPI.
- O PostgreSQL estiver configurado e versionado por migrations.
- Autenticação e autorização estiverem funcionando no backend.
- Os módulos de clientes, fornecedores, usuários e OS estiverem integrados.
- O número da OS for único e gerado de forma segura.
- As regras de transição de status forem aplicadas no backend.
- O histórico registrar eventos relevantes.
- Os filtros e a paginação funcionarem.
- Os testes automatizados essenciais forem executados com sucesso.
- A aplicação funcionar em ambiente de teste com interface responsiva.
- As instruções de configuração e execução estiverem registradas no `README.md`.

## 19. Decisões técnicas

### 19.1 Decisões registradas para o MVP

| # | Decisão | Onde é aplicada |
|---|---|---|
| 1 | Sistema **multiempresa**, com `company_id` em todas as entidades de negócio e isolamento em todas as consultas. | Seções 3, 7 e 9; Fase 2 de `tasks.md`; Seção 4 de `acceptance.md` |
| 2 | Frontend em HTML, CSS e JavaScript puro (módulos ES6), sem framework. | Seções 4 e 5 |
| 3 | Autenticação por sessão server-side em cookie `HttpOnly` com token CSRF; sem JWT. | Seções 9.2, 11 e 15.1 |
| 4 | Técnico atua somente em OS atribuídas: observações, transições de status e conclusão. Não edita dados gerais nem cancela OS. | Seção 9.9 |
| 5 | Uma OS possui no máximo um técnico responsável. | Seção 3 |
| 6 | Anexos e impressão/exportação em PDF ficam fora do MVP. | Seções 3 e 12 |
| 7 | Cadastro público de empresa **não** será implementado; provisionamento administrativo controlado. | Seção 3; TASK-030 e TASK-082 de `tasks.md` |
| 8 | E-mail de login é único globalmente; um usuário pertence a uma única empresa no MVP. | Seção 7.2; TASK-017 de `tasks.md` |
| 9 | Numeração de OS por empresa, gerada atomicamente por `service_order_sequences`. | Seções 7.5 e 7.7; TASK-048 de `tasks.md` |
| 10 | Dashboard não é habilitado para Técnicos no MVP. | Seções 9.7 e 9.9 |
| 11 | Documentação principal permanece na raiz; `docs/` é destinada à documentação complementar. | Seção 5 |
| 12 | CSRF obrigatório nas operações de escrita autenticadas; `POST /auth/login` é público e possui exceção documentada. | Seção 9.2 |
| 13 | Limitação de tentativas de login em memória por credencial/origem, substituível por store compartilhado em instalações com múltiplos processos. | Seção 9.2; Fase 3 de `tasks.md` |

### 19.2 Pendente para fases posteriores

1. Ambiente de hospedagem e estratégia de backup — definir antes da Fase 13 de `tasks.md`.

As decisões registradas devem ser refletidas no modelo de dados, nos endpoints, nos testes e na interface. Reabri-las exige atualização deste documento e dos demais documentos afetados.

---

**Documento:** `spec.md`  
**Projeto:** OrdemFácil  
**Versão:** 1.3 — Especificação técnica com Fases 1, 2 e 3 implementadas  
**Documento relacionado:** `requirements.md`