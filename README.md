# Plataforma Digital Segura para Periódicos

Este repositorio contiene la arquitectura base multi-contenedor para la Plataforma Digital Segura. 

## Estructura del Proyecto

```text
plataforma-periodico/ (raíz)
├── backend/            # Backend en Django + Django REST Framework
├── frontend/           # Frontend en React + TypeScript + Vite + Tailwind
├── infrastructure/     # Archivos de configuración de infraestructura (Nginx, etc.)
├── docker-compose.yml  # Orquestador de contenedores
├── .env.example        # Plantilla de variables de entorno
├── .gitignore          # Exclusiones de control de versiones
└── README.md           # Este archivo de documentación
```

## Requisitos Previos

* Docker y Docker Compose instalados y en ejecución.
* Base de datos PostgreSQL externa (operativa en el host `76.13.172.55` puerto `5435`).

## Configuración Inicial

1. Copie el archivo `.env.example` para crear su archivo de configuración local:
   ```bash
   cp .env.example .env
   ```
2. Coloque la contraseña real de la base de datos PostgreSQL en la variable `DB_PASSWORD` en su archivo `.env` local.

## Comandos para Levantar el Proyecto

Para compilar y levantar toda la arquitectura (Backend, Frontend, Redis, Celery Workers, Celery Beat, Nginx):

```bash
docker compose up --build
```

Si prefiere ejecutarlo en segundo plano:

```bash
docker compose up --build -d
```

## Endpoints Técnicos de Verificación (Health Checks)

Nginx actúa como proxy inverso en el puerto `80`. Una vez que el sistema se encuentra arriba, puede probar los siguientes endpoints:

* **Estado General de Salud:** `http://localhost/api/v1/health/`
* **Verificación de PostgreSQL:** `http://localhost/api/v1/health/database/`
* **Verificación de Redis:** `http://localhost/api/v1/health/redis/`
