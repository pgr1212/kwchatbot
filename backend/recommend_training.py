# backend/recommend_training.py

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

def _fetch_similar_training_chunks(query_embedding, top_k=4):
    conn = psycopg2.connect(**PG_DSN)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT dc.doc_id, dc.chunk_id, dc.chunk_text, dc.category, 1 - (e.embedding <#> %s::vector) AS similarity
        FROM embeddings e
        JOIN doc_chunks dc ON e.chunk_id = dc.chunk_id
        WHERE dc.category = '내일배움'
        ORDER BY e.embedding <#> %s::vector
        LIMIT %s;
        """,
        (query_embedding, query_embedding, top_k * 4)
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

def recommend_trainings(user_query, top_k=2):
    query_embedding = model.encode(user_query).tolist()
    rows = _fetch_similar_training_chunks(query_embedding, top_k=top_k)
    
    if not rows:
        return []

    results = []
    seen_ids = set()

    for row in rows:
        doc_id = row[0]
        sim = round(float(row[4]), 4)
        
        if sim < SIM_THRESHOLD:
            continue
        if doc_id in seen_ids:
            continue
        seen_ids.add(doc_id)

        # 전체 텍스트 가져오기
        chunks = _fetch_all_chunks_by_doc(doc_id)
        full_text = "\n".join([txt for _, txt in chunks])
        lines = [line.strip() for line in full_text.strip().split('\n') if line.strip()]

        if not lines:
            continue

        # --- 정밀 파싱 로직 ---
        
        # 1. 기본값 설정
        raw_title = lines[0]
        subtitle = "기관 정보 없음"
        address = "주소 정보 없음"
        link = "#"
        
        # 2. 제목 정제 (훈련과정명: 제거)
        title = raw_title
        if "훈련과정명" in title:
            # "훈련과정명:" 또는 "훈련과정명 :" 제거
            title = title.replace("훈련과정명", "").replace(":", "").strip()

        # 3. 키워드 기반 필드 추출 (부제목, 주소, 링크)
        for line in lines:
            if line.startswith("부제목:"):
                subtitle = line.replace("부제목:", "").strip()
            elif line.startswith("주소:"):
                address = line.replace("주소:", "").strip()
            elif line.startswith("상세링크:") or ("http" in line and "hrd" in line):
                if "http" in line:
                    link = line.replace("상세링크:", "").strip()

        # 4. 주소를 못 찾았을 경우 대비 (키워드 검색 보완)
        if address == "주소 정보 없음":
            location_keywords = ["서울", "경기", "인천", "구", "대로", "길"]
            for line in lines:
                if line == raw_title: continue
                # "전화번호"가 포함된 줄은 주소가 아니므로 제외
                if any(loc in line for loc in location_keywords) and "전화번호" not in line and len(line) < 60:
                    address = line
                    break

        # 5. 상세 내용은 제목을 제외한 나머지 전체
        detail = "\n".join(lines[1:])

        results.append({
            "doc_id": doc_id,
            "title": title,
            "subtitle": subtitle,
            "address": address,
            "link": link,
            "detail": detail,
            "score": sim
        })

        if len(results) >= top_k:
            break

    return results