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

def _fetch_similar_chunks(query_embedding, top_k=3):  # 디버깅을 위해 기본값을 3으로 변경
    conn = psycopg2.connect(**PG_DSN)
    cur = conn.cursor()
    # 코사인 유사도 검색
    cur.execute(
        """
        SELECT dc.doc_id, dc.chunk_id, dc.chunk_text, dc.category, 1 - (e.embedding <#> %s::vector) AS similarity
        FROM embeddings e
        JOIN doc_chunks dc ON e.chunk_id = dc.chunk_id
        WHERE dc.category = '연구실 정보'
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
    
    # top_k=3으로 여러 후보를 가져와 봅니다.
    rows = _fetch_similar_chunks(query_embedding, top_k=3)
    
    if not rows:
        print("[DEBUG] 검색 결과 없음")
        return None

    # 1등 후보 선택
    best_doc_id = rows[0][0]
    best_sim = round(float(rows[0][4]), 4)
    
    # [중요] 유사도 임계값 설정 (예: 0.3 미만이면 추천 안 함)
    # 필요하다면 아래 주석을 해제해서 사용하세요.
    # if best_sim < 0.35:
    #     print(f"[DEBUG] 유사도({best_sim})가 너무 낮아 추천하지 않음")
    #     return None

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
        if not line_clean: continue

        if "연구실명:" in line_clean or "연구실:" in line_clean:
             # ':' 뒤에 내용이 있으면 가져오고 없으면 건너뜀
             parts = line_clean.split(":", 1)
             if len(parts) > 1 and parts[1].strip():
                 name = parts[1].strip()

        if "교수명:" in line_clean or "담당교수:" in line_clean:
             parts = line_clean.split(":", 1)
             if len(parts) > 1 and parts[1].strip():
                 professor = parts[1].strip()

        if "연구분야:" in line_clean:
             parts = line_clean.split(":", 1)
             if len(parts) > 1 and parts[1].strip():
                 field = parts[1].strip()
        elif "연구내용:" in line_clean and field == "연구분야 정보 없음":
             parts = line_clean.split(":", 1)
             if len(parts) > 1 and parts[1].strip():
                 field = parts[1].strip()

    # 안전장치: 파싱 실패 시 첫 줄 활용
    if name == "연구실명 정보 없음" and lines:
        first_line = lines[0].strip()
        if len(first_line) < 30 and ":" not in first_line:
            name = first_line

    return {
        "doc_id": best_doc_id,
        "name": name,
        "professor": professor,
        "field": field,
        "introduction": full_text,
        "score": best_sim
    }