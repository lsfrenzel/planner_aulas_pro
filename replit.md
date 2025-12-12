# Aula Planner Pro

## Overview
Sistema web completo para planejamento de aulas, desenvolvido com Flask (Python) e interface moderna usando Tailwind CSS. O sistema permite gerenciar um cronograma de 20 semanas com funcionalidades CRUD completas.

## Project Architecture

### Backend (Flask)
- **app.py**: Aplicação principal com API REST
  - `GET /api/weeks` - Lista todas as semanas
  - `GET /api/weeks/<id>` - Retorna semana específica
  - `POST /api/weeks` - Adiciona nova semana
  - `PUT /api/weeks/<id>` - Edita semana existente
  - `DELETE /api/weeks/<id>` - Remove semana
  - `GET /api/export/json` - Exporta cronograma em JSON
  - `GET /api/export/pdf` - Exporta cronograma em PDF

### Frontend
- **templates/index.html**: Interface principal com Tailwind CSS
- **static/js/app.js**: JavaScript para interatividade
- **static/css/style.css**: Estilos customizados

### Banco de Dados
- **data/weeks.json**: Armazena o cronograma (20 semanas pré-preenchidas)

## Features
- CRUD completo de semanas
- Tema claro/escuro com persistência
- Filtros por Unidade Curricular e Recursos
- Busca por texto
- Exportação para JSON e PDF
- Interface responsiva
- Sidebar navegável

## Running the Project
```bash
python app.py
```
O servidor inicia na porta 5000.

## Dependencies
- Flask
- ReportLab (geração de PDF)

## Recent Changes
- 2025-12-12: Criação inicial do projeto com todas as funcionalidades
