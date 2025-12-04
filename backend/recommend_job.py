# backend/recommend_job.py
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

SIM_THRESHOLD = 0.25
MODEL_PATH = "jhgan/ko-sbert-sts"
model = SentenceTransformer(MODEL_PATH)

def _fetch_similar_job_chunks(query_embedding, top_k=3):
    conn = psycopg2.connect(**PG_DSN)
    cur = conn.cursor()
    # 중복 제거를 고려하여 넉넉하게 가져옵니다.
    cur.execute(
        """
        SELECT dc.doc_id, dc.chunk_id, dc.chunk_text, dc.category, 1 - (e.embedding <#> %s::vector) AS similarity
        FROM embeddings e
        JOIN doc_chunks dc ON e.chunk_id = dc.chunk_id
        WHERE dc.category = '직업정보'
        ORDER BY e.embedding <#> %s::vector
        LIMIT %s;
        """,
        (query_embedding, query_embedding, top_k)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def recommend_jobs(user_query, top_k=2):
    query_embedding = model.encode(user_query).tolist()
    
    # 중복(내용이 같은 문서) 제거를 위해 넉넉히 5배수 검색
    fetch_limit = top_k * 5
    rows = _fetch_similar_job_chunks(query_embedding, top_k=fetch_limit)
    
    if not rows:
        return []

    results = []
    
    # [수정] doc_id가 아닌 '직업명(Title)'을 저장하여 중복 체크
    seen_titles = set()

    for row in rows:
        chunk_text = row[2]
        sim = float(row[4])
        doc_id = row[0]
        
        if sim < SIM_THRESHOLD:
            continue

        lines = chunk_text.strip().split('\n')
        title = lines[0].strip()  # 첫 줄을 직업명으로 간주
        
        # [핵심 수정] 이미 결과 목록에 있는 '직업명'이면 건너뜀 (ID가 달라도 이름 같으면 패스)
        if title in seen_titles:
            continue

        # 새로운 직업명이면 등록
        seen_titles.add(title)
        
        reason = "\n".join(lines[1:]).strip() if len(lines) > 1 else chunk_text

        results.append({
            "doc_id": doc_id,
            "title": title,
            "reason": reason,
            "score": round(sim, 4)
        })
        
        if len(results) >= top_k:
            break

    return results