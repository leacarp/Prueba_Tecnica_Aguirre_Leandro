# Prueba Técnica – Aguirre Leandro (UNILINK)

Asistente automatizado de soporte técnico que responde preguntas utilizando documentación interna mediante un sistema RAG (Retrieval-Augmented Generation).

## Stack utilizado

- **n8n** — orquestación del flujo y exposición del webhook
- **Python + Flask** — procesamiento de documentos y búsqueda semántica
- **FAISS** — vector store local para búsqueda por similitud
- **OpenAI API** — embeddings (`text-embedding-3-small`) y generación de respuestas (`gpt-4o-mini`)

## Requisitos previos

- Python 3.12+
- n8n instalado localmente
- API Key de OpenAI

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/prueba-tecnica-aguirre-leandro.git
cd prueba-tecnica-aguirre-leandro
```

### 2. Crear y activar el entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

Editá el archivo `.env` y agregá tu API Key de OpenAI:
OPENAI_API_KEY=your_openai_api_key_here

## Uso

### Paso 1 — Indexar la documentación

Este comando lee los archivos de la carpeta `/docs`, genera embeddings y crea el índice vectorial local. Se ejecuta una sola vez, o cada vez que se actualiza la documentación.

```bash
python src/ingest.py
```
Procesando: Documentación 1.pdf

→ 2 chunks generados
..

✓ Índice guardado en data/index.faiss

✓ Chunks guardados en data/chunks.json

### Paso 2 — Levantar el servidor Python

```bash
python src/api.py
```

El servidor queda corriendo en `http://localhost:5000`. Mantener esta terminal abierta.

### Paso 3 — Importar el workflow en n8n

1. Abrir n8n en `http://localhost:5678`
2. Ir a **Workflows → Import from file**
3. Seleccionar el archivo `workflow.json`
4. Configurar la credencial de OpenAI en el nodo **OpenAI Chat Model**
5. Activar el workflow

### Paso 4 — Consultar el asistente

Hacer un POST al webhook:

```bash
curl -X POST http://localhost:5678/webhook-test/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "no puedo iniciar sesión"}'
```

O desde Postman:
- **URL:** `http://localhost:5678/webhook-test/ask`
- **Method:** POST
- **Body (JSON):**
```json
{ "question": "no puedo iniciar sesión" }
```

## Ejemplos de respuesta

**Pregunta con respuesta en la documentación:**
```json
{
  "answer": "El error de credenciales incorrectas (ERR-AUTH-001) puede deberse a..."
}
```

**Pregunta sin información disponible:**
```json
{
  "answer": "No encontré información en la documentación disponible para responder tu consulta."
}
```

## Manejo de errores

| Situación | Comportamiento |
|---|---|
| Pregunta con respuesta | HTTP 200 + respuesta generada |
| Pregunta sin contexto relevante | HTTP 404 + mensaje informativo |
| Query vacía | HTTP 400 desde Flask |
| Servidor Python apagado | Error en nodo HTTP Request de n8n |