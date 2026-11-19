# OrdemFácil

Sistema web **multiempresa** de gerenciamento de ordens de serviço para pequenas e médias empresas prestadoras de serviços (assistências técnicas, oficinas, manutenção, instalação, climatização e informática).

**Status:** Fases 0, 1, 2 e 3 concluídas. Próxima etapa: Fase 4 — Cadastro de clientes.

## Estado da implementação

- API FastAPI com endpoints de saúde (`/health` e `/api/v1/health`), erros padronizados e CORS restrito por configuração.
- Configuração carregada com `pydantic-settings`, com validações obrigatórias para produção (`APP_DEBUG=false`, `SECRET_KEY` definida e cookie seguro).
- Persistência em PostgreSQL com SQLAlchemy 2.0, sessões por requisição e Alembic configurado.
- Migration inicial cria `companies` e `users`, com `company_id` obrigatório, e-mail único globalmente e chave composta `(company_id, id)` para futuras relações escopadas.
- Fundação multiempresa implementada em `app/core/tenant.py`: nenhuma consulta de negócio deve receber `company_id` do navegador.
- Autenticação por sessão server-side: token opaco armazenado como hash em `user_sessions`, cookie `HttpOnly`/`SameSite=Lax`, token CSRF exigido nas operações de escrita autenticadas e revogação no logout.
- Senhas com hash Argon2id; usuários e empresas inativos não autenticam; limite de tentativas de login com resposta 429.
- Endpoints de autenticação (`/auth/login`, `/auth/logout`, `/auth/me`) e gerenciamento de usuários restrito a Administradores, sempre no escopo da empresa da sessão.

## Documentação

| Arquivo | Conteúdo |
|---|---|
| `requirements.md` | Requisitos funcionais, regras de negócio, requisitos não funcionais e escopo do MVP |
| `spec.md` | Arquitetura, modelo de dados, API, segurança e decisões técnicas (Seção 19) |
| `design.md` | UX/UI, identidade visual, telas, componentes e acessibilidade |
| `tasks.md` | Backlog por fases (TASK-001 a TASK-121), Definition of Done e evidências |
| `acceptance.md` | Critérios de aceite, massa de dados de teste e homologação |
| `AGENTS.md` | Instruções para agentes de IA e desenvolvedores |
| `docs/` | Documentação complementar |

## Decisões consolidadas do MVP

- Sistema multiempresa com isolamento obrigatório por `company_id`.
- Autenticação por sessão server-side em cookie `HttpOnly`, com token CSRF; sem JWT.
- Frontend em HTML, CSS e JavaScript puro (módulos ES6), sem framework.
- Numeração de OS por empresa, gerada de forma atômica (nunca por contagem).
- Cadastro público de empresa e dashboard para Técnico: fora do escopo do MVP.
- Matriz de permissões por perfil e transição de status em `spec.md` §9.9.

## Estrutura

```text
backend/
  app/
    core/          configuração, erros, segurança e escopo multiempresa
    database/      base declarativa, engine e sessão
    models/        Company, User e UserSession
    routes/        endpoints HTTP (health, auth, users)
    schemas/       schemas Pydantic de autenticação e usuários
    services/      autenticação, sessões, senhas, limite de login e usuários
    repositories/  persistência (a evoluir nas próximas fases)
  alembic/         migrations
  tests/           testes automatizados
frontend/          interface web (a implementar)
docs/              documentação complementar
*.md               documentação principal na raiz
```

## Pré-requisitos

- Python 3.12 ou superior
- PostgreSQL 15 ou superior
- pip

## Configuração

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
```

No Windows:

```powershell
Copy-Item backend\.env.example backend\.env
```

Crie o banco no PostgreSQL e ajuste `DATABASE_URL`, `SECRET_KEY` e `CORS_ORIGINS` em `backend/.env`. As variáveis `SESSION_EXPIRE_MINUTES`, `LOGIN_MAX_ATTEMPTS` e `LOGIN_LOCKOUT_MINUTES` controlam sessão e limite de tentativas. **Nunca versionar `.env`.**

Se quiser subir um PostgreSQL temporário com Docker:

```bash
docker run --name ordemfacil-pg \
  -e POSTGRES_USER=ordemfacil \
  -e POSTGRES_PASSWORD=senha-teste \
  -e POSTGRES_DB=ordemfacil \
  -p 5432:5432 \
  postgres:16-alpine
```

## Execução

```bash
cd backend
alembic upgrade head
uvicorn app.main:app --reload
```

Endpoints disponíveis nesta fase:

- `GET /health`
- `GET /api/v1/health`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET`, `POST /api/v1/users`
- `GET`, `PUT /api/v1/users/{id}`
- `PATCH /api/v1/users/{id}/status`

Após o login, o frontend deve ler o cookie `ordemfacil_csrf` e enviá-lo no cabeçalho `X-CSRF-Token` em toda requisição `POST`, `PUT`, `PATCH` ou `DELETE` autenticada. `POST /auth/login` é público e não exige CSRF.

A documentação OpenAPI fica disponível em `http://127.0.0.1:8000/docs` em ambiente de desenvolvimento.

## Testes

```bash
cd backend
pytest
```

A suíte usa SQLite em memória e não exige PostgreSQL. As migrations também são testadas em modo offline e aplicadas/revertidas em SQLite; a validação em PostgreSQL 16 foi executada durante as Fases 1, 2 e 3 (migrations `0001_companies_users` e `0002_user_sessions`).

Os testes de isolamento multiempresa usam a massa de dados de `acceptance.md` (Oficina Alfa e Assistência Beta).

## Convenções

- Identificadores em inglês (`snake_case` em Python, `camelCase` em JavaScript); textos ao usuário em pt-BR.
- Backend valida permissões, regras de negócio e isolamento; frontend é apenas apresentação.
- O `company_id` é sempre obtido da identidade autenticada, nunca do cliente HTTP.
- Toda alteração de esquema do banco exige migration Alembic.
- Uma tarefa só é marcada como concluída após a Definition of Done de `tasks.md`.
