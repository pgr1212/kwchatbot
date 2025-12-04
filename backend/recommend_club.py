# type: uploaded file
# fileName: backend/recommend_club.py
# ============================================
# 🤝 SBERT 기반 동아리 추천 시스템 (코사인 유사도 버전)
# ============================================

import os
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# ===== .env 불러오기 =====
load_dotenv()

# ===== 기본 설정 =====
PG_DSN = {
    "host": "localhost",
    "port": "5432",
    "dbname": "kwchatbot",   # ⚠️ DB 이름 확인
    "user": "postgres",
    "password": "3864"       # ⚠️ 비밀번호 확인
}

# ===== SBERT 모델 =====
MODEL_PATH = "jhgan/ko-sbert-sts"
try:
    model = SentenceTransformer(MODEL_PATH)
except:
    model = SentenceTransformer("jhgan/ko-sbert-sts")

# ============================================
# 🔹 1️⃣ 동아리 카테고리에서 유사 청크 검색
# ============================================
def _fetch_similar_chunks(query_embedding, top_k=1):
    conn = psycopg2.connect(**PG_DSN)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT 
            dc.doc_id,
            dc.chunk_id,
            dc.chunk_text,
            dc.category,
            (e.embedding <=> %s::vector) AS distance
        FROM embeddings e
        JOIN doc_chunks dc ON e.chunk_id = dc.chunk_id
        WHERE dc.category = '동아리'
        ORDER BY e.embedding <=> %s::vector
        LIMIT %s;
        """,
        (query_embedding, query_embedding, top_k)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# ============================================
# 🔹 2️⃣ 동일 동아리(doc_id)의 모든 청크 가져오기
# ============================================
def _fetch_all_chunks_by_doc(doc_id):
    conn = psycopg2.connect(**PG_DSN)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT chunk_index, chunk_text
        FROM doc_chunks
        WHERE doc_id = %s
        ORDER BY chunk_index ASC;
        """,
        (doc_id,)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# ============================================
# 🔹 3️⃣ 추천 함수 (파싱 로직 수정: 이름/분야/소속)
# ============================================
def recommend_one_club(user_query):
    """
    사용자 쿼리를 받아 가장 적합한 동아리 1개를 추천합니다.
    데이터 내에서 '이름', '분야', '소속' 키워드를 찾아 정보를 분리합니다.
    """
    # 1. 임베딩 생성
    query_embedding = model.encode(user_query).tolist()

    # 2. 유사 청크 검색 (Top 1)
    rows = _fetch_similar_chunks(query_embedding, top_k=1)
    if not rows:
        return None

    # 가장 유사한 동아리 선택
    best_doc_id = rows[0][0]
    best_sim = round(1 - float(rows[0][4]), 4)

    # 3. 해당 동아리의 전체 텍스트 가져오기
    chunks = _fetch_all_chunks_by_doc(best_doc_id)
    if not chunks:
        return None

    full_text = "\n".join([txt for _, txt in chunks])
    lines = full_text.splitlines()

    # --- 🔍 파싱 로직 강화 ---
    name = "동아리명 정보 없음"
    field = "분야 정보 없음"
    affiliation = "소속 정보 없음" # 소속 추가

    # 모든 줄을 검사하여 정보 추출
    for line in lines:
        line_clean = line.strip()
        
        # 1. 동아리명 찾기 ('이름' 키워드)
        if "이름" in line_clean or "동아리명" in line_clean:
            if ":" in line_clean:
                extracted_name = line_clean.split(":", 1)[1].strip()
                if extracted_name:
                    name = extracted_name
        
        # 2. 분야 찾기 ('분야' 키워드)
        if "분야" in line_clean:
            if ":" in line_clean:
                extracted_field = line_clean.split(":", 1)[1].strip()
                if extracted_field:
                    field = extracted_field
        
        # 3. 소속 찾기 ('소속' 키워드) - 새로 추가됨
        if "소속" in line_clean:
            if ":" in line_clean:
                extracted_affiliation = line_clean.split(":", 1)[1].strip()
                if extracted_affiliation:
                    affiliation = extracted_affiliation

    # 키워드로 이름을 못 찾았다면, 첫 줄을 제목으로 사용 (안전장치)
    if name == "동아리명 정보 없음" and lines:
        first_line = lines[0].strip()
        if "분야" not in first_line and "소속" not in first_line and ":" not in first_line:
            name = first_line
    
    # 4. 결과 반환
    # introduction에 full_text를 넣어주면 모달에서 전체 데이터를 볼 수 있습니다.
    return {
        "doc_id": best_doc_id,
        "name": name,             # 동아리 이름
        "field": field,           # 분야
        "affiliation": affiliation, # 소속 (프론트엔드에 표시하려면 컴포넌트 수정 필요할 수 있음)
        "introduction": full_text,  # 상세 내용 (전체 데이터)
        "score": best_sim
    }

# ============================================
# 🔹 실행 예시
# ============================================
if __name__ == "__main__":
    query = "로봇 만드는 동아리 추천해줘"
    print(f"\n[사용자 입력] {query}\n")

    rec = recommend_one_club(query)

    if rec:
        print(f"🎯 추천 동아리: {rec['name']} (유사도: {rec['score']})")
        print(f"📂 분야: {rec['field']}")
        print(f"🏫 소속: {rec['affiliation']}")
        print(f"📘 전체 데이터:\n{rec['introduction'][:100]}...")
    else:
        print("추천 결과를 찾지 못했습니다.")