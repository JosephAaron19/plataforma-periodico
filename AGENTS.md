# Reglas de Gobernanza y Operación del Sistema

Este documento establece las directrices estrictas y de carácter obligatorio para el desarrollo, pruebas y operaciones técnicas en este repositorio.

## 1. Gobernanza de la Base de Datos (PostgreSQL Externa)

* **Prohibición de Operaciones Manuales Directas:** Está estrictamente prohibido realizar limpiezas de datos, sentencias `DELETE`, `UPDATE` masivos o cualquier tipo de corrección de datos de forma directa sobre la base de datos PostgreSQL externa de producción o desarrollo sin autorización expresa y documentada del responsable del proyecto.
* **Flujo de Aprobación Obligatorio:** Antes de proponer o ejecutar cualquier operación de modificación de datos o de carácter destructivo (incluyendo limpieza de datos de prueba), se debe presentar:
  1. La consulta SQL exacta a ejecutar.
  2. Los registros específicos que serán afectados.
  3. El impacto técnico y funcional en el sistema.
  * Se deberá detener la ejecución y esperar la aprobación explícita antes de proceder.
* **Control de Integridad:** El conteo de las 54 tablas en el esquema `pdg` no es prueba suficiente de la ausencia de cambios en los datos. No se debe realizar ninguna suposición de que los registros no han sido alterados simplemente porque la estructura del esquema permanece estable.
* **Pruebas Manuales Funcionales:** Las pruebas manuales que inserten usuarios ficticios u otros registros simulados **no deben** realizarse contra la base de datos PostgreSQL externa. Las pruebas de integración reales deben realizarse sobre una base de datos aislada configurada específicamente para este fin una vez sea provista.

## 2. Gestión de Logs y Correo en Desarrollo

* **Riesgo del Backend de Consola (`console.EmailBackend`):** En entornos de desarrollo, Django utiliza el backend de correo de consola para facilitar la depuración, lo cual provoca que los tokens completos de verificación de correo se impriman en la salida estándar (terminal/logs).
* **Mitigación de Fuga de Credenciales:**
  * Este backend está estrictamente limitado al entorno de desarrollo (`development.py`) y condicionado a `DJANGO_DEBUG=True`. **Nunca** debe configurarse o usarse en producción.
  * Se prohíbe que cualquier salida de log que contenga tokens completos, hashes de tokens, contraseñas o hashes de contraseñas sea guardada en archivos del repositorio o versionada en Git.
  * No se debe incluir bajo ninguna circunstancia el cuerpo completo de correos de prueba o tokens planos en walkthroughs, reportes o archivos de documentación.
