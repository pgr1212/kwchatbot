# type: uploaded file
# fileName: backend/recommend_hakyeon.py

import os
import psycopg2
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

PG_DSN = {
    "host": "localhost",
    "port": "5432",
    "dbname": "kwchatbot",
    "user": "postgres",
    "password": "3864"
}

MODEL_PATH = "jhgan/ko-sbert-sts"
try:
    model = SentenceTransformer(MODEL_PATH)
except:
    model = SentenceTransformer("jhgan/ko-sbert-sts")

def _fetch_similar_chunks(query_embedding, top_k=1):
    conn = psycopg2.connect(**PG_DSN)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT dc.doc_id, dc.chunk_id, dc.chunk_text, dc.category, 1 - (e.embedding <#> %s::vector) AS similarity
        FROM embeddings e
        JOIN doc_chunks dc ON e.chunk_id = dc.chunk_id
        WHERE dc.category = '학연생'
        ORDER BY e.embedding <#> %s::vector
        LIMIT %s;
        """,
        (query_embedding, query_embedding, top_k)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def _fetch_all_chunks_by_doc(doc_id):
    conn = psycopg2.connect(**PG_DSN)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT chunk_index, chunk_text FROM doc_chunks
        WHERE doc_id = %s ORDER BY chunk_index ASC;
        """,
        (doc_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def recommend_one_hakyeon(user_query):
    query_embedding = model.encode(user_query).tolist()
    
    rows = _fetch_similar_chunks(query_embedding, top_k=1)
    if not rows:
        return None

    best_doc_id = rows[0][0]
    best_sim = round(float(rows[0][4]), 4)

    chunks = _fetch_all_chunks_by_doc(best_doc_id)
    if not chunks:
        return None

    full_text = "\n".join([txt for _, txt in chunks])
    lines = full_text.splitlines()

    # --- 🔍 파싱 로직 ---
    name = "연구실명 정보 없음"
    professor = "교수명 정보 없음"
    field = "연구분야 정보 없음"

    for line in lines:
        line_clean = line.strip()
        
        # 1. 연구실명 찾기
        if line_clean.startswith("연구실명:") or line_clean.startswith("연구실:"):
            name = line_clean.split(":", 1)[1].strip()
            
        # 2. 교수명 찾기
        if line_clean.startswith("교수명:") or line_clean.startswith("담당교수:"):
            professor = line_clean.split(":", 1)[1].strip()
            
        # 3. 연구분야/내용 찾기
        if line_clean.startswith("연구분야:") or line_clean.startswith("연구내용:"):
            field = line_clean.split(":", 1)[1].strip()

    # 안전장치: 첫 줄을 이름으로 사용 (키워드 없을 경우)
    if name == "연구실명 정보 없음" and lines:
        first_line = lines[0].strip()
        if "교수" not in first_line and ":" not in first_line:
            name = first_line

    return {
        "doc_id": best_doc_id,
        "name": name,
        "professor": professor,
        "field": field,
        "introduction": full_text, # 상세 보기용 전체 텍스트
        "score": best_sim
    }