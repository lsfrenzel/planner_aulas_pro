# Aula Planner Pro

## Overview
Sistema web completo para planejamento de aulas, desenvolvido com Flask (Python) e interface moderna usando Tailwind CSS. O sistema permite gerenciar um cronograma de 20 semanas com funcionalidades CRUD completas, autenticação de usuários e painel administrativo.

## Project Architecture

### Backend (Flask)
- **app.py**: Aplicação principal com API REST e autenticação

#### Rotas de Autenticação
- `GET/POST /login` - Tela de login
- `GET /logout` - Encerrar sessão
- `GET /admin` - Painel administrativo (apenas admins)

#### API de Usuários (Admin)
- `GET /api/users` - Lista todos os usuários
- `POST /api/users` - Adiciona novo usuário
- `PUT /api/users/<id>` - Edita usuário
- `DELETE /api/users/<id>` - Remove usuário

#### API de Semanas
- `GET /api/weeks` - Lista todas as semanas
- `GET /api/weeks/<id>` - Retorna semana específica
- `POST /api/weeks` - Adiciona nova semana
- `PUT /api/weeks/<id>` - Edita semana existente
- `DELETE /api/weeks/<id>` - Remove semana
- `GET /api/export/json` - Exporta cronograma em JSON
- `GET /api/export/pdf` - Exporta cronograma em PDF

### Frontend
- **templates/index.html**: Interface principal do cronograma
- **templates/login.html**: Tela de login
- **templates/admin.html**: Painel de gerenciamento de usuários
- **static/js/app.js**: JavaScript para interatividade
- **static/css/style.css**: Estilos customizados

### Banco de Dados
- **data/weeks.json**: Armazena o cronograma (20 semanas pré-preenchidas)
- **data/users.db**: Banco SQLite para usuários

## Features
- Autenticação de usuários com senha criptografada
- Painel admin para gerenciamento de usuários
- CRUD completo de semanas
- Tema claro/escuro com persistência
- Filtros por Unidade Curricular e Recursos
- Busca por texto
- Exportação para JSON e PDF
- Interface responsiva
- Sidebar navegável

## Credenciais Padrão
- **Email**: admin@aula.com
- **Senha**: admin123

## Running the Project
```bash
python app.py
```
O servidor inicia na porta 5000.

## Dependencies
- Flask
- ReportLab (geração de PDF)
- Werkzeug (hash de senhas)

## Recent Changes
- 2025-12-12: Adicionado sistema de autenticação e painel admin
- 2025-12-12: Criação inicial do projeto com todas as funcionalidades
