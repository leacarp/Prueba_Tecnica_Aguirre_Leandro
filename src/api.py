import os
import json
import faiss
import numpy as np
from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATA_FOLDER = "data"
TOP_K = 3  

app = Flask(__name__)


# ── CARGA DEL ÍNDICE AL INICIAR 

def load_index():
    index_path = os.path.join(DATA_FOLDER, "index.faiss")
    chunks_path = os.path.join(DATA_FOLDER, "chunks.json")

    if not os.path.exists(index_path) or not os.path.exists(chunks_path):
        raise FileNotFoundError(
            "No se encontró el índice. Ejecutá src/ingest.py primero."
        )

    index = faiss.read_index(index_path)

    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    return index, chunks


index, chunks = load_index()


# ── HELPERS 

def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def search(query, top_k=TOP_K):
    query_vector = get_embedding(query)
    matrix = np.array([query_vector], dtype="float32")

    distances, indices = index.search(matrix, top_k)

    results = []
    for i, idx in enumerate(indices[0]):
        if idx == -1:
            continue
        results.append({
            "text": chunks[idx]["text"],
            "source": chunks[idx]["source"],
            "score": float(distances[0][i])
        })

    return results


# ── ENDPOINTS 

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "chunks_loaded": len(chunks)})


@app.route("/search", methods=["POST"])
def search_endpoint():
    body = request.get_json()

    if not body:
        return jsonify({"error": "El body debe ser JSON"}), 400

    query = body.get("query", "").strip()

    if not query:
        return jsonify({"error": "El campo 'query' es obligatorio"}), 400

    if len(query) > 1000:
        return jsonify({"error": "La query no puede superar 1000 caracteres"}), 400

    try:
        results = search(query)
    except Exception as e:
        return jsonify({"error": f"Error en la búsqueda: {str(e)}"}), 500

    if not results:
        return jsonify({
            "query": query,
            "results": [],
            "message": "No se encontraron fragmentos relevantes"
        }), 200

    return jsonify({
        "query": query,
        "results": results
    }), 200


# ── ARRANQUE 

if __name__ == "__main__":
    print("Servidor iniciado en http://localhost:5000")
    print(f"Índice cargado: {len(chunks)} chunks disponibles")
    app.run(host="0.0.0.0", port=5000, debug=False)