import os
import json
import fitz  
import faiss
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DOCS_FOLDER = "docs"
DATA_FOLDER = "data"
CHUNK_SIZE = 400      
CHUNK_OVERLAP = 50    


# ── 1. LECTURA DE ARCHIVOS 

def read_txt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def read_md(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return json.dumps(data, ensure_ascii=False, indent=2)

def read_pdf(path):
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def read_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".txt":
        return read_txt(path)
    elif ext == ".md":
        return read_md(path)
    elif ext == ".json":
        return read_json(path)
    elif ext == ".pdf":
        return read_pdf(path)
    else:
        print(f"Formato no soportado: {path}")
        return ""


# ── 2. LIMPIEZA DE TEXTO 

def clean_text(text):
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        line = line.strip()
        if line:
            cleaned.append(line)
    return " ".join(cleaned)


# ── 3. CHUNKING 

def split_into_chunks(text, source_name):
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + CHUNK_SIZE
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)
        chunks.append({
            "text": chunk_text,
            "source": source_name
        })
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


# ── 4. EMBEDDINGS 

def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


# ── 5. PROCESO PRINCIPAL 

def main():
    os.makedirs(DATA_FOLDER, exist_ok=True)

    all_chunks = []

    for filename in os.listdir(DOCS_FOLDER):
        filepath = os.path.join(DOCS_FOLDER, filename)
        print(f"Procesando: {filename}")

        raw_text = read_file(filepath)
        if not raw_text:
            continue

        clean = clean_text(raw_text)
        chunks = split_into_chunks(clean, source_name=filename)
        all_chunks.extend(chunks)
        print(f"  → {len(chunks)} chunks generados")

    print(f"\nTotal chunks: {len(all_chunks)}")
    print("Generando embeddings... (puede tardar unos segundos)")

    vectors = []
    for i, chunk in enumerate(all_chunks):
        embedding = get_embedding(chunk["text"])
        vectors.append(embedding)
        if (i + 1) % 10 == 0:
            print(f"  → {i + 1}/{len(all_chunks)} embeddings generados")

    dimension = len(vectors[0])  
    index = faiss.IndexFlatL2(dimension)
    matrix = np.array(vectors, dtype="float32")
    index.add(matrix)

    faiss.write_index(index, os.path.join(DATA_FOLDER, "index.faiss"))
    with open(os.path.join(DATA_FOLDER, "chunks.json"), "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Índice guardado en {DATA_FOLDER}/index.faiss")
    print(f"✓ Chunks guardados en {DATA_FOLDER}/chunks.json")


if __name__ == "__main__":
    main()