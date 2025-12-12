# Aula Planner Pro

## Overview
Sistema web completo para planejamento de aulas, desenvolvido com Flask (Python), PostgreSQL e interface moderna usando Tailwind CSS. O sistema permite gerenciar um cronograma de 20 semanas com funcionalidades CRUD completas, autenticação de usuários, painel administrativo e dashboard com visualização em tabela.

## Project Architecture

### Backend (Flask + PostgreSQL)
- **app.py**: Aplicação principal com API REST, autenticação e Flask-SQLAlchemy
- **models.py**: Modelos do banco de dados (User, Schedule)
- **main.py**: Ponto de entrada para o servidor

#### Rotas de Autenticação
- `GET/POST /login` - Tela de login
- `GET /logout` - Encerrar sessão
- `GET /admin` - Painel administrativo (apenas admins)

#### Rotas de Visualização
- `GET /` - Interface principal com cards
- `GET /dashboard` - Dashboard com tabela de todas as semanas

#### API de Usuários (Admin)
- `GET /api/users` - Lista todos os usuários
- `POST /api/users` - Adiciona novo usuário
- `PUT /api/users/<id>` - Edita usuário
- `DELETE /api/users/<id>` - Remove usuário

#### API de Semanas
- `GET /api/weeks` - Lista todas as semanas do usuário
- `GET /api/weeks/<id>` - Retorna semana específica
- `POST /api/weeks` - Adiciona nova semana
- `PUT /api/weeks/<id>` - Edita semana existente
- `DELETE /api/weeks/<id>` - Remove semana
- `GET /api/export/json` - Exporta cronograma em JSON
- `GET /api/export/pdf` - Exporta cronograma em PDF
- `GET /api/export/xlsx` - Exporta cronograma em Excel (XLSX)

#### Rotas de Perfil
- `GET /perfil` - Pagina de edicao de perfil
- `POST /perfil/atualizar` - Atualiza nome, cargo e foto
- `POST /perfil/alterar-senha` - Altera senha do usuario

### Frontend
- **templates/index.html**: Interface principal do cronograma (cards)
- **templates/dashboard.html**: Dashboard com visualização em tabela
- **templates/login.html**: Tela de login
- **templates/admin.html**: Painel de gerenciamento de usuários
- **templates/perfil.html**: Pagina de edicao de perfil do usuario
- **static/js/app.js**: JavaScript para interatividade
- **static/css/style.css**: Estilos customizados
- **static/uploads/profiles/**: Pasta para fotos de perfil dos usuarios

### Banco de Dados (PostgreSQL)
- **users**: Tabela de usuários (id, name, email, password_hash, role, cargo, photo, active, created_at)
- **schedules**: Tabela de cronogramas por usuário (id, user_id, semana, atividades, unidade_curricular, capacidades, conhecimentos, recursos, created_at)
- Cada usuário vê apenas seus próprios cronogramas
- O admin inicial recebe os dados migrados do weeks.json original

## Features
- Autenticação de usuários com senha criptografada
- Painel admin para gerenciamento de usuários
- Pagina de perfil com upload de foto, edicao de cargo e alteracao de senha
- Dashboard com visualização em tabela de todas as semanas
- CRUD completo de semanas
- Tema claro/escuro com persistência
- Filtros por Unidade Curricular e Recursos
- Busca por texto
- Exportação para JSON, PDF e Excel (XLSX)
- Interface responsiva
- Sidebar navegável
- Estatísticas (total semanas, unidades curriculares, recursos)

## Credenciais Padrão
- **Email**: admin@aula.com
- **Senha**: admin123

## Running the Project
```bash
gunicorn --bind 0.0.0.0:5000 main:app
```
O servidor inicia na porta 5000.

## Railway Deployment
O projeto está configurado para deploy no Railway:
- **Procfile**: Configuração do processo web
- **requirements.txt**: Dependências Python
- **runtime.txt**: Versão do Python (3.11.6)

### Variáveis de Ambiente Necessárias no Railway
- `DATABASE_URL`: URL de conexão PostgreSQL (fornecida automaticamente pelo Railway)
- `SESSION_SECRET`: Chave secreta para sessões Flask

## Dependencies
- Flask 3.0.0
- Flask-SQLAlchemy 3.1.1
- SQLAlchemy 2.0.23
- psycopg2-binary 2.9.11
- gunicorn 23.0.0
- ReportLab 4.4.6
- openpyxl 3.1.5
- Werkzeug 3.0.1
- email-validator 2.3.0

## Recent Changes
- 2025-12-12: Adicionadas barras de progresso no dashboard para cada turma (semanas e capacidades)
- 2025-12-12: Nova API /api/turmas/progress para calcular estatisticas de progresso por turma
- 2025-12-12: Barras de progresso atualizam em tempo real ao marcar semanas/capacidades como concluidas
- 2025-12-12: Adicionada exportacao para Excel (XLSX) com formatacao profissional
- 2025-12-12: Foto de perfil do usuario agora aparece no cabecalho ao lado do nome
- 2025-12-12: Adicionada pagina de perfil com upload de foto, edicao de cargo e alteracao de senha
- 2025-12-12: Novos campos no modelo User: cargo e photo
- 2025-12-12: Links de perfil adicionados em todas as paginas
- 2025-12-12: Corrigido erro "Semana nao encontrada" no toggle de status - API agora usa ID correto
- 2025-12-12: Dashboard agora exibe painel com informacoes da turma (carga horaria, dias, horarios, datas)
- 2025-12-12: PDF de exportacao agora inclui cabecalho com detalhes da turma selecionada
- 2025-12-12: Adicionados campos de carga horaria, dias/horarios de aula, e datas inicio/fim nas Turmas
- 2025-12-12: Implementado fluxo turma-primeiro (usuario deve criar turma antes de semanas)
- 2025-12-12: APIs de semanas agora exigem turma_id
- 2025-12-12: Interface atualizada com seletor de turma na sidebar
- 2025-12-12: Migracao automatica cria turma padrao para schedules orfaos
- 2025-12-12: Corrigido relacionamento entre Schedule e Turma para evitar erros de FK
- 2025-12-12: Removido cascade delete para turmas (turmas agora são opcionais)
- 2025-12-12: Adicionado dashboard com visualização em tabela de todas as semanas
- 2025-12-12: Migrado de SQLite para PostgreSQL (compatível com Railway)
- 2025-12-12: Adicionados arquivos de deploy (Procfile, requirements.txt, runtime.txt)
- 2025-12-12: Implementado isolamento de dados por usuário
- 2025-12-12: Removidas credenciais padrão da tela de login
- 2025-12-12: Adicionado sistema de autenticação e painel admin
- 2025-12-12: Criação inicial do projeto
