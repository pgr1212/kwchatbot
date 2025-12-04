# backend/recommend_training.py
import psycopg2
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os

load_dotenv()

PG_DSN = {
    "host": "localhost",
    "port": "5432",
    "dbname": "kwchatbot",
    "user": "postgres",
    "password": "3864"
}

model = SentenceTransformer("jhgan/ko-sbert-sts")

def recommend_trainings(user_query, top_k=2):
    conn = psycopg2.connect(**PG_DSN)
    cur = conn.cursor()
    query_embedding = model.encode(user_query).tolist()

    cur.execute("""
        SELECT dc.doc_id, dc.chunk_text
        FROM embeddings e
        JOIN doc_chunks dc ON e.chunk_id = dc.chunk_id
        WHERE dc.category = '내일배움'
        ORDER BY e.embedding <#> %s::vector
        LIMIT 10;
    """, (query_embedding,))
    
    rows = cur.fetchall()
    conn.close()

    results = []
    seen_ids = set()

    for doc_id, text in rows:
        if doc_id in seen_ids: continue
        seen_ids.add(doc_id)

        lines = text.strip().split('\n')
        title = lines[0].strip() # 첫 줄: 제목
        
        address = "온라인 / 장소 문의"
        link = "#" # 링크가 없으면 #

        # 주소와 링크 추출
        for line in lines:
            if any(loc in line for loc in ["서울", "경기", "인천", "구", "로", "길"]):
                address = line.strip()
            if "http" in line:
                link = line.strip()
        
        results.append({
            "title": title,
            "address": address,
            "link": link,
            "detail": text
        })
        
        if len(results) >= top_k: break

    return results