# Catálogo de Habilidades del Agente y Estándares de Arquitectura

Este archivo define el conjunto de habilidades, patrones de diseño y estándares técnicos que el agente de desarrollo debe desplegar para asegurar que el proyecto **Sociedad 5.0** sea mantenible, seguro y libre de deuda técnica.

---

## 1. Diseño de Software Limpio y Modular

* **Single Responsibility Principle (SRP)**: Cada función, clase y módulo en el proyecto debe tener una única razón para cambiar. Los flujos de entrada/salida (LLM), las capas de datos (Firestore) y la orquestación deben estar estrictamente separados.
* **Tipado Estático**: Uso de anotaciones de tipo de Python (`typing`) en todas las declaraciones para aumentar la robustez y autocompletado en los editores de código.
* **Structured Outputs en LLM**: El análisis semántico no debe depender de expresiones regulares o filtros improvisados sobre respuestas de texto plano. Se debe definir siempre un esquema formal mediante clases Pydantic (`BaseModel`) y usar `response_schema` en la API de Gemini para forzar validación a nivel de motor.

---

## 2. Seguridad y Buenas Prácticas de Datos

* **Protección de Credenciales**: Las llaves de API y credenciales de cuentas de servicio deben cargarse estrictamente desde variables de entorno a través de `dotenv`. Nunca deben escribirse de forma estática en el código base.
* **Aislamiento de Base de Datos**: Al instanciar clientes de Firestore, se debe usar la sintaxis moderna que soporta bases de datos con IDs personalizados (`google.cloud.firestore.Client(database=...)`) para evitar colisiones accidentales de bases de datos compartidas o de producción.

---

## 3. Prevención Proactiva de Deuda Técnica

* **Uso de APIs Actualizadas**: Evitar métodos obsoletos o desaconsejados. Por ejemplo, utilizar `datetime.now(timezone.utc)` en lugar de `datetime.utcnow()` para prevenir advertencias de deprecación futuras.
* **Control Extensible de Excepciones**: No usar bloques `try/except` vacíos o demasiado generales que oculten la causa raíz de las fallas. Capturar y registrar errores específicos de la API (por ejemplo, `503 Unavailable`, `429 Quota Exceeded`, `404 Not Found`) para permitir una depuración ágil.
* **Documentación Dinámica**: Mantener actualizados de forma paralela los archivos de metadatos como `requirements.txt` y la bitácora `memory.md` en cada sesión de desarrollo concluida.
