# Reglas e Instrucciones Inquebrantables para Agentes de IA

Este documento establece las directrices y normas de comportamiento inquebrantables que cualquier agente de inteligencia artificial (incluidos subagentes y asistentes de desarrollo) debe respetar y seguir estrictamente al interactuar con esta base de código.

---

## 1. Principio de Aprobación Previa (Explicar y Preguntar)
* **Regla de Oro**: El agente **NUNCA** debe realizar modificaciones en el código fuente, crear o eliminar archivos (a excepción de bitácoras menores), ni ejecutar scripts o comandos terminales sin antes:
  1. Explicar de manera clara y detallada en español al desarrollador humano cuál es la tarea que se va a realizar y qué archivos o configuraciones se verán afectados.
  2. Solicitar aprobación explícita del desarrollador.
* **Flujo obligatorio**:
  ```text
  [Agente detecta cambio] ➔ [Explica la propuesta en español] ➔ [Pregunta: ¿Procedo?] ➔ [Espera aprobación] ➔ [Ejecuta el cambio]
  ```
* **Lecturas de diagnóstico**: Se permite de forma autónoma leer el contenido de archivos del proyecto (`view_file`, `grep_search` o listar directorios) para entender el flujo, pero **nunca** para alterar el estado del proyecto sin consentimiento.

---

## 2. Desarrollo Limpio y Estandarizado
* **No generar deuda técnica**: Todo código nuevo debe estar debidamente tipado, estructurado en funciones modulares de una sola responsabilidad y libre de funciones y métodos obsoletos.
* **Gestión de Dependencias**: Cualquier librería externa agregada debe instalarse estrictamente dentro del entorno virtual `.venv` y registrarse al momento en `requirements.txt` con codificación estándar UTF-8.
* **Documentación en Código**: Todas las funciones deben incluir docstrings claros que detallen sus parámetros, retornos y excepciones.

---

## 3. Preservación del Entorno
* El agente debe evitar alterar variables de entorno críticas de forma permanente sin justificarlo.
* Las llaves de seguridad y credenciales (`credenciales_firebase.json` y claves dentro de `api_keys.env`) deben mantenerse seguras y no exponerse en logs públicos ni subirse a repositorios de control de versiones.
