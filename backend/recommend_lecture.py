import os
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# ===== Load .env =====
load_dotenv()

# ===== Basic Settings =====
PG_DSN = {
    "host": "localhost",
    "port": "5432",
    "dbname": "kwchatbot",
    "user": "postgres",
    "password": "3864"
}

# ===== SBERT 모델 =====
MODEL_PATH = "jhgan/ko-sbert-sts"
model = SentenceTransformer(MODEL_PATH)


def _fetch_similar_chunks(query_embedding, top_k=10):
    conn = psycopg2.connect(**PG_DSN)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT 
            dc.doc_id,
            dc.chunk_id,
            dc.chunk_text,
            dc.category,
            1 - (e.embedding <#> %s::vector) AS similarity
        FROM embeddings e
        JOIN doc_chunks dc ON e.chunk_id = dc.chunk_id
        WHERE dc.category = '강의정보'
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
        SELECT chunk_index, chunk_text
        FROM doc_chunks
        WHERE doc_id = %s
          AND chunk_index != 2
        ORDER BY chunk_index ASC;
        """,
        (doc_id,)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def recommend_courses(user_query, top_k=4):
    """
    사용자 쿼리와 가장 유사한 강의 top_k개를 반환합니다.
    (강의명+교수명 기준 중복 제거 적용)
    """
    query_embedding = model.encode(user_query).tolist()

    # 중복 제거를 고려하여 넉넉하게 검색 (5배수)
    rows = _fetch_similar_chunks(query_embedding, top_k=top_k * 5)
    
    if not rows:
        return []

    results = []
    
    # 1차적으로 이미 처리한 doc_id는 스킵 (DB 호출 최소화)
    processed_doc_ids = set()
    
    # [핵심 수정] (강의명, 교수명) 쌍을 저장하여 내용 중복 체크
    seen_content_keys = set()

    for row in rows:
        doc_id = row[0]
        similarity = round(float(row[4]), 4)

        if doc_id in processed_doc_ids:
            continue
        processed_doc_ids.add(doc_id)

        # 문서 내용 가져오기
        chunks = _fetch_all_chunks_by_doc(doc_id)
        if not chunks:
            continue
            
        full_text = "\n".join([txt for idx, txt in chunks])
        lines = full_text.splitlines()

        # --- 파싱 로직 ---
        title = "강의명 정보 없음"
        department = "소속 학과 정보 없음"
        professor = "담당 교수 정보 없음"

        for line in lines:
            line = line.strip()
            if "교과목명" in line or "과목명" in line or "강의명" in line:
                if ":" in line:
                    t = line.split(":", 1)[1].strip()
                    if t: title = t
            
            if "학과명" in line or "개설학과" in line or "소속학과" in line:
                if ":" in line:
                    department = line.split(":", 1)[1].strip()
            
            if "담당교수" in line:
                 if ":" in line:
                    professor = line.split(":", 1)[1].strip()

        if title == "강의명 정보 없음" and lines:
            first_line = lines[0].strip()
            if "학과" not in first_line and "교수" not in first_line and ":" not in first_line:
                title = first_line

        # [핵심 수정] 강의명과 교수가 모두 같다면 중복으로 간주하고 건너뜀
        # (공백 제거하여 비교)
        unique_key = (title.replace(" ", ""), professor.replace(" ", ""))
        
        if unique_key in seen_content_keys:
            continue
            
        seen_content_keys.add(unique_key)

        results.append({
            "doc_id": doc_id,
            "title": title,
            "department": department,
            "professor": professor,
            "similarity": similarity,
            "detail": full_text
        })

        if len(results) >= top_k:
            break
    
    return results