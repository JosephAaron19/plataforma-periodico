# Reporte de Diagnóstico Inicial
**Proyecto:** Plataforma Digital Segura para Periódicos
**Rol:** Arquitecto de Software y Analista Técnico
**Fecha de Diagnóstico:** 15 de junio de 2026
**Estado:** Fase 01 - Preparación e Inspección

---

## 1. Resumen Ejecutivo
El presente diagnóstico detalla el estado actual del proyecto "Plataforma Digital Segura para Periódicos". Tras una inspección exhaustiva de la estructura de archivos en la raíz del proyecto `c:\Users\Joseph\Desktop\Periodico-digital`, se concluye que **no existe código base desarrollado ni configuraciones técnicas iniciales (como repositorios Git, archivos Docker o variables de entorno)**. 

Sin embargo, el proyecto cuenta con un conjunto sólido de documentos de especificación en formato Word (`.docx`). Estos archivos definen los requisitos de negocio, las reglas funcionales, el backlog priorizado para el MVP y una propuesta de arquitectura tecnológica. Las carpetas destinadas para el desarrollo de la aplicación (`Back` y `Front-web`) se encuentran actualmente vacías, lo que indica que el proyecto está en una fase de pre-desarrollo (Fase de Definición Funcional y Técnica).

---

## 2. Estructura Actual del Proyecto
La raíz del proyecto cuenta únicamente con dos directorios de desarrollo vacíos y cinco documentos de especificación funcional y técnica de negocio en formato Word (.docx). No existen archivos ocultos ni directorios de control de versiones (.git) inicializados.

---

## 3. Inventario de Carpetas
A continuación, se detalla el estado de las carpetas identificadas en el directorio raíz:

| Directorio | Ruta Relativa | Estado Actual | Propósito Sugerido |
| :--- | :--- | :--- | :--- |
| `Back` | `\Back` | **Vacío** | Código fuente del backend (APIs, lógica de negocio y base de datos). |
| `Front-web` | `\Front-web` | **Vacío** | Código fuente del frontend web (interfaz de usuario, visor y biblioteca). |

---

## 4. Inventario de Archivos Técnicos
Actualmente, **no existen archivos técnicos** de desarrollo en el proyecto. 
* No hay archivos de configuración de dependencias (`package.json`, `requirements.txt`, `Pipfile`, etc.).
* No hay archivos de infraestructura o despliegue (`Dockerfile`, `docker-compose.yml`, `nginx.conf`).
* No hay código fuente de ningún tipo (`.py`, `.js`, `.ts`, `.html`, `.css`, etc.).

---

## 5. Inventario de Documentos
Se han identificado 5 documentos en formato Word (`.docx`) en la raíz del proyecto. A continuación se realiza el inventario detallado de cada uno:

| Nombre del Archivo | Tamaño | Ubicación | Tema Aparente / Propósito | Categoría Sugerida |
| :--- | :--- | :--- | :--- | :--- |
| `Analisis_Negocio_Periodico_Virtual.docx` | 5.06 MB (5,309,227 bytes) | Raíz del proyecto | Especificación funcional y técnica detallada del MVP. Contiene 5 imágenes incrustadas que actúan como mockups funcionales simulados de las interfaces clave (visor protegido, carga PDF, página pública). | Diseño Técnico y Funcional |
| `Analisis_Plataforma_Digital_Periodicos.docx` | 50.8 KB (52,020 bytes) | Raíz del proyecto | Análisis preliminar de negocio y sistema (Versión 1.0 original, previa a la subsanación de observaciones). | Análisis de Negocio (Preliminar) |
| `Analisis_Plataforma_Digital_Periodicos (1).docx` | 55.4 KB (56,833 bytes) | Raíz del proyecto | Duplicado en texto del documento anterior (con ligeras diferencias de metadatos o compresión binaria). | Análisis de Negocio (Duplicado) |
| `Analisis_Plataforma_Digital_Periodicos_Observaciones_Subsanadas.docx` | 52.7 KB (54,056 bytes) | Raíz del proyecto | Análisis de negocio corregido y actualizado. Incluye un control de observaciones que detalla cómo se atendieron temas clave (complejidad por módulo, flujos alternos, dependencias de backlog y responsables de riesgo). | Análisis de Negocio (Finalizado) |
| `Hoja_de_Ruta_MVP_Periodico.docx` | 37.8 KB (38,801 bytes) | Raíz del proyecto | Planificación en 10 etapas controladas para la construcción del MVP, desde la infraestructura inicial hasta las pruebas y despliegue del piloto. | Gestión del Proyecto / Roadmap |

> [!NOTE]
> El archivo `Analisis_Negocio_Periodico_Virtual.docx` es significativamente más pesado debido a la inclusión de recursos gráficos (imágenes y mockups) dentro del archivo, ocupando 5.06 MB del espacio.

---

## 6. Tecnologías Detectadas (Propuestas en Documentación)
Aunque no hay código implementado, la documentación técnica adjunta define claramente el stack tecnológico planificado para la construcción del MVP:

* **Backend:** Django REST Framework (DRF) o NestJS (propuestos para la API de autenticación, reglas de negocio y reportes).
* **Frontend:** React + Vite + Tailwind CSS (con soporte propuesto de TypeScript).
* **Base de Datos:** PostgreSQL (para usuarios, empresas, ediciones, pagos, progreso de lectura y logs).
* **Procesamiento PDF (Worker/Async):** Celery + Redis o BullMQ.
* **Almacenamiento (Storage):** Servidor privado o almacenamiento S3 compatible (para PDFs originales y páginas procesadas).
* **Servidor Web:** Nginx con configuración HTTPS.
* **Integración de Pagos:** Pasarela de pago con confirmación mediante Webhook.

---

## 7. Backend Encontrado
* **Estado:** No implementado.
* **Ruta:** `\Back` (Directorio vacío).
* **Componentes identificados en diseño:** Módulo de autenticación (JWT), gestión de empresas (SaaS multi-tenant), CRUD de ediciones, procesamiento asíncrono de PDFs mediante worker, y endpoints para validar el acceso al visor.

---

## 8. Frontend Encontrado
* **Estado:** No implementado.
* **Ruta:** `\Front-web` (Directorio vacío).
* **Componentes identificados en diseño:** Landing pública de promoción, catálogo de ediciones, biblioteca de usuario con visualización de compras, y un visor web protegido con soporte de marcas de agua personalizadas y controles de bloqueo de descarga/copia.

---

## 9. Infraestructura Encontrada
* **Estado:** No implementada.
* **Archivos Docker:** No se detectan `Dockerfile` ni `docker-compose.yml`.
* **Configuraciones de Red / Proxy:** No se detectan archivos de configuración de Nginx.

---

## 10. Configuraciones Encontradas
* **Variables de entorno:** No existen archivos `.env` ni `.env.example` en la raíz ni en los directorios de desarrollo.
* **Base de datos:** No hay scripts de base de datos (`.sql`) ni configuraciones de conexión a PostgreSQL.

---

## 11. Archivos Duplicados o Posiblemente Duplicados
Se ha detectado redundancia en los documentos de análisis:
1. `Analisis_Plataforma_Digital_Periodicos.docx` y `Analisis_Plataforma_Digital_Periodicos (1).docx` poseen contenido de texto idéntico y representan la versión original 1.0 del análisis de negocio.
2. Estos dos archivos quedan obsoletos ante la existencia de `Analisis_Plataforma_Digital_Periodicos_Observaciones_Subsanadas.docx`, el cual incorpora las correcciones aplicadas a las observaciones de negocio y técnicas.

---

## 12. Archivos Mal Ubicados
Los cinco documentos `.docx` están ubicados directamente en la raíz del proyecto. Esta disposición entorpece la organización del código fuente en la raíz. 
* **Sugerencia:** Deberán trasladarse a una carpeta exclusiva para documentación (por ejemplo, `\docs` o `\documentacion`).

---

## 13. Riesgos Identificados
Como Arquitecto de Software, identifico los siguientes riesgos en el estado de inicio del proyecto:

1. **Ausencia de Control de Versiones:** El proyecto no cuenta con un repositorio Git local inicializado (`.git`), lo que impide el control de versiones y el registro estructurado de cambios sobre el código e infraestructura que se va a crear.
2. **Ambigüedad en el Stack de Backend:** Los documentos proponen alternativamente Django REST Framework o NestJS. Es necesario consolidar la decisión antes de iniciar el Sprint 1 para evitar discrepancias en la arquitectura final.
3. **Falta de Plantillas de Configuración:** Al no existir archivos `.env.example`, los desarrolladores carecen de una guía clara sobre las variables de entorno necesarias para la base de datos, el almacenamiento seguro y las pasarelas de pago.
4. **Desorden en Raíz del Proyecto:** La mezcla de documentos de Word con directorios de desarrollo en el mismo nivel dificulta la claridad visual de los límites del código del sistema.

---

## 14. Recomendaciones de Organización
Para preparar el entorno antes de iniciar con la fase de construcción de código (Paso 2), se recomiendan las siguientes acciones:

1. **Inicialización de Git:** Ejecutar `git init` en la raíz de la plataforma para comenzar a trackear los cambios.
2. **Creación de Carpeta de Documentación:** Crear la carpeta `\docs` en la raíz y mover allí los archivos Word aprobados para mantener la raíz del proyecto limpia.
3. **Creación de `.env.example`:** Diseñar una plantilla de variables de entorno en la raíz del proyecto que mapee la configuración del Backend, Frontend, Postgres, Redis, y APIs de terceros.
4. **Remoción de Duplicados:** Archivar o eliminar las versiones preliminares obsoletas de los análisis una vez que el usuario valide la versión definitiva subsanada.
5. **Configuración de Docker Base:** Crear los archivos `docker-compose.yml` y las directivas Docker en `Back` y `Front-web` para homogeneizar los ambientes locales de desarrollo.

---

## 15. Elementos que Deben Conservarse
Se deben conservar y priorizar los siguientes documentos de referencia, pues constituyen la especificación autorizada del MVP:
1. `Analisis_Plataforma_Digital_Periodicos_Observaciones_Subsanadas.docx` (Requisitos de negocio oficiales).
2. `Analisis_Negocio_Periodico_Virtual.docx` (Especificación funcional, técnica y mockups del MVP).
3. `Hoja_de_Ruta_MVP_Periodico.docx` (Planificación y control del progreso).

---

## 16. Elementos que Requieren Revisión Manual
* **Definición Tecnológica del Backend:** El equipo debe sesionar para confirmar de manera unánime si se usará **Django REST Framework** o **NestJS** para el backend de la API. (Django REST Framework está alineado con la base de datos PostgreSQL y Celery/Redis indicados en varios sprints).
* **Confirmación de Pasarela de Pagos:** Definir cuál será el proveedor de pagos del piloto para configurar adecuadamente los webhooks de confirmación y logs de auditoría en la etapa correspondiente.

---

## 17. Árbol Simplificado del Proyecto

A continuación se presenta el árbol estructural del proyecto en su estado inicial actual:

```text
Periodico-digital/
├── Back/                      # Directorio de backend (Vacío)
├── Front-web/                 # Directorio de frontend (Vacío)
├── Analisis_Negocio_Periodico_Virtual.docx
├── Analisis_Plataforma_Digital_Periodicos (1).docx
├── Analisis_Plataforma_Digital_Periodicos.docx
├── Analisis_Plataforma_Digital_Periodicos_Observaciones_Subsanadas.docx
└── Hoja_de_Ruta_MVP_Periodico.docx
```
