# AGENTS.md — OrdemFácil

Instruções para agentes de IA e desenvolvedores que trabalham neste repositório.

## 1. Visão geral

**OrdemFácil** é um sistema web **multiempresa** de gerenciamento de ordens de serviço, voltado a pequenas e médias empresas prestadoras de serviços (assistências técnicas, oficinas, manutenção, etc.).

- **Idioma:** português do Brasil (pt-BR) em documentação, interface e mensagens ao usuário.
- **Estado atual:** Fases 0, 1, 2 e 3 concluídas. Backend FastAPI, PostgreSQL/SQLAlchemy, Alembic, fundação multiempresa, autenticação por sessão e gerenciamento de usuários implementados; as fases 4 a 13 seguem `tasks.md`.
- **MVP:** autenticação por perfil, dashboard, clientes, fornecedores, ordens de serviço (OS), atribuição de técnico, status, observações, solução, histórico, pesquisa/filtros.

### Stack adotada

| Camada | Tecnologia |
|---|---|
| Frontend | HTML5, CSS3, JavaScript puro (módulos ES6) |
| Backend | Python + FastAPI |
| Persistência | PostgreSQL |
| ORM / Migrations | SQLAlchemy + Alembic |
| Validação | Pydantic |
| Servidor ASGI | Uvicorn |
| Testes | Pytest |

## 2. Documentos de referência (fonte da verdade)

Os documentos estão na **raiz** do projeto (a pasta `docs/` é reservada para documentação complementar):

| Arquivo | Para que serve |
|---|---|
| `requirements.md` | Requisitos funcionais (RF), regras de negócio (RN), não funcionais (RNF) e escopo do MVP |
| `spec.md` | Arquitetura, modelo de dados, endpoints, regras técnicas, segurança e decisões consolidadas |
| `design.md` | UX/UI, paleta, componentes, telas, responsividade e acessibilidade |
| `tasks.md` | Backlog por fases (TASK-001 a TASK-121) e Definition of Done |
| `acceptance.md` | Critérios de aceite (CA-*), massa de dados de teste e checklist de homologação |

**Antes de implementar qualquer tarefa:** leia os documentos aplicáveis e verifique em `tasks.md` a fase e a tarefa correspondente.

### Decisões consolidadas

A divergência anterior sobre "uma empresa por instalação" foi resolvida: `spec.md` e `requirements.md` agora adotam o modelo **multiempresa**, alinhados a `design.md`, `tasks.md` e `acceptance.md`. O isolamento é requisito bloqueador (Fase 2 de `tasks.md` e CA-MULTI-001 a CA-MULTI-010).

As decisões do MVP estão registradas em `spec.md` §19.1 e resumidas em `tasks.md` (bloco "Decisões consolidadas"). Não as reabra sem atualizar a documentação.

## 3. Regras obrigatórias (não negociáveis)

### Isolamento multiempresa

- Toda entidade de negócio deve ter `company_id` e todas as consultas devem filtrar por ele.
- O `company_id` **nunca** deve vir do navegador; deve ser obtido do usuário autenticado.
- Tentativas de acessar, editar, concluir ou cancelar registros de outra empresa devem retornar erro **sem revelar os dados**.
- Relacionamentos (cliente, técnico, empresa, histórico) só podem referenciar registros da mesma empresa.
- A fundação multiempresa (Fase 2) é **bloqueadora**: não avance para módulos de negócio sem isolamento implementado e testado.

### Backend é a camada de segurança

- Regras de negócio, validações e autorização devem ser aplicadas no backend, nunca apenas na interface.
- Esconder um botão no frontend não substitui verificação de permissão na API.
- Perfis: `ADMIN`, `ATTENDANT`, `TECHNICIAN`. Técnicos enxergam e atualizam **somente** as OS atribuídas a eles.
- Matriz completa de permissões por operação e transição: `spec.md` §9.9.
- Autenticação por sessão server-side em cookie `HttpOnly` com token CSRF; **sem JWT**.
- Usuários inativos não podem autenticar.

### Ordens de serviço

- Número da OS: gerado por `service_order_sequences` com atualização atômica, transacional e único **por empresa** (`UNIQUE (company_id, order_number)`). Nunca gerar contando registros.
- Status: `OPEN`, `IN_PROGRESS`, `WAITING`, `COMPLETED`, `CANCELED`.
- Transições permitidas (validar no serviço de domínio):
  - `OPEN` → `IN_PROGRESS` ou `CANCELED`
  - `IN_PROGRESS` → `WAITING`, `COMPLETED` ou `CANCELED`
  - `WAITING` → `IN_PROGRESS` ou `CANCELED`
  - `COMPLETED` e `CANCELED` são estados finais no MVP (sem reabertura).
- Conclusão exige `resolution`; cancelamento exige `cancellation_reason`.
- Toda alteração relevante (abertura, status, atribuição/troca de técnico, observações, conclusão, cancelamento) deve gerar registro em `service_order_history` com usuário e data/hora do servidor.
- Clientes e fornecedores com histórico devem ser **inativados**, nunca excluídos fisicamente.

### Segurança e dados

- Senhas apenas como hash (Argon2id ou bcrypt com configuração segura).
- Segredos somente em variáveis de ambiente; `.env` nunca versionado; `.env.example` apenas com exemplos fictícios.
- CORS restrito às origens autorizadas por ambiente; HTTPS em produção; `APP_DEBUG=false` em produção.
- Mensagens de erro não podem expor SQL, stack traces, caminhos locais, tokens ou dados de outras empresas.
- Usar ORM/consultas parametrizadas e validação Pydantic.
- Evitar logs com senhas, tokens ou dados pessoais desnecessários; mascarar documentos em listagens quando não forem necessários.
- Coletar apenas dados pessoais necessários (LGPD).

### Escopo do MVP

**Não implementar sem atualizar a documentação:** aplicativo mobile nativo, notas fiscais, WhatsApp, integrações fiscais/contábeis/pagamentos, financeiro, estoque avançado, compras, relatórios avançados, operação offline, anexos, geração de PDF, múltiplos técnicos por OS, reabertura de OS, cadastro de usuário em várias empresas.

## 4. Convenções de código

- Identificadores de código em inglês (`snake_case` em Python, `camelCase` em JavaScript); textos visíveis ao usuário em pt-BR.
- Backend organizado por domínio: `core/`, `database/`, `models/`, `schemas/`, `routes/`, `services/`, `repositories/`.
- Rotas finas: autenticação/autorização nas dependências, regras de negócio nos **serviços**, persistência nos repositórios/modelos.
- Respostas de API padronizadas, prefixo `/api/v1`, UUIDs, datas ISO 8601 em UTC, paginação nas listagens.
- Códigos HTTP: 200/201/204 sucesso; 400 transição inválida; 401 não autenticado; 403 sem permissão; 404 não encontrado; 409 conflito; 422 validação; 500 erro inesperado.
- Toda alteração de esquema do banco exige migration Alembic.
- Fixar versões das dependências em `backend/requirements.txt`.
- Seguir `design.md` para paleta, tipografia, componentes, estados de tela (carregamento/vazio/erro/sucesso), responsividade e acessibilidade (WCAG 2.2 AA quando viável). Status deve ser identificado por texto, não apenas cor.
- Datas exibidas em `DD/MM/AAAA`, horários em 24h, telefones e documentos no formato brasileiro.

## 5. Comandos

O backend das Fases 1 e 2 já está implementado. O fluxo atual é:

```bash
# Dependências
pip install -r backend/requirements.txt

# Banco de dados (executar em backend/)
alembic upgrade head

# API (desenvolvimento, executar em backend/)
uvicorn app.main:app --reload

# Testes (executar em backend/)
pytest
```

A documentação OpenAPI do FastAPI fica disponível em ambiente de desenvolvimento. A autenticação por sessão já está ativa: `get_current_user` valida cookie de sessão e CSRF; os testes podem substituir essa dependência quando necessário.

## 6. Testes e conclusão de tarefas

- Testes unitários: documentos, transições de status, conclusão/cancelamento, permissões, numeração da OS.
- Testes de integração: login, rotas protegidas, cadastros, abertura/atribuição/status/histórico de OS, filtros, paginação e acesso cruzado.
- **Testes de isolamento multiempresa são obrigatórios.** Usar a massa de `acceptance.md`: Oficina Alfa (Empresa A) e Assistência Beta (Empresa B), com administrador, atendente e técnicos de cada empresa.
- Uma tarefa só pode ser marcada `[x]` em `tasks.md` após atender integralmente à **Definition of Done** (seção 19): implementação, validações e permissões no backend, isolamento respeitado, testes criados/executados, sem erros conhecidos, documentação atualizada e alteração revisada/integrada.
- Registrar resultados de homologação na tabela de execução de testes de `acceptance.md` (`Aprovado`, `Reprovado`, `Bloqueado` ou `Pendente`).
- Decisões técnicas relevantes devem ser registradas em `spec.md` ou documentação complementar.
