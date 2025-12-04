# ============================================
# 🎯 SBERT 기반 동아리 추천 시스템 + LLM 설명 생성
# ============================================

import os
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv

# ===== 환경변수 로드 =====
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ===== 기본 설정 =====
OPENAI_MODEL = "gpt-3.5-turbo"
PG_DSN = {
    "host": "localhost",
    "dbname": "kwchatbot",
    "user": "postgres",
    "password": "kk003300kk*"
}
SIM_THRESHOLD = 0.25

# ===== SBERT 모델 =====
MODEL_PATH = "jhgan/ko-sbert-sts"
model = SentenceTransformer(MODEL_PATH)

# ===== OpenAI 클라이언트 =====
client = OpenAI(api_key=OPENAI_API_KEY)


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
            1 - (e.embedding <#> %s::vector) AS similarity
        FROM embeddings e
        JOIN doc_chunks dc ON e.chunk_id = dc.chunk_id
        WHERE dc.category = '동아리'
        ORDER BY e.embedding <#> %s::vector
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
# 🔹 3️⃣ 추천 함수 + LLM 설명 생성
# ============================================
def recommend_and_describe_club(user_query):
    # 1️⃣ 사용자 쿼리 임베딩 생성
    query_embedding = model.encode(user_query).tolist()

    # 2️⃣ 유사 청크 검색
    rows = _fetch_similar_chunks(query_embedding, top_k=1)
    if not rows:
        return "❗ 관련 동아리 정보를 찾지 못했습니다."

    # 3️⃣ 가장 유사한 동아리(doc_id) 선택
    best_doc_id = rows[0][0]
    best_sim = round(float(rows[0][4]), 4)

    # 4️⃣ 해당 동아리의 모든 청크 가져오기
    chunks = _fetch_all_chunks_by_doc(best_doc_id)
    if not chunks:
        return f"❗ doc_id={best_doc_id} 에 대한 동아리 청크를 찾지 못했습니다."

    # 5️⃣ 동아리 텍스트 통합
    full_text = "\n-----\n".join(
        [f"[{idx}] {txt}" for idx, txt in chunks]
    )

    # 6️⃣ LLM 프롬프트 구성
    system_prompt = """
    당신은 광운대학교 KW Chatbot의 동아리/진로 추천 도우미입니다.
    아래 CONTEXT는 특정 동아리에 대한 정보입니다.
    동아리 정보를 간단히 요약하고,
    이 동아리가 사용자의 관심사와 목표(진로, 대외활동, 학교생활 적응 등)에
    어떻게 도움이 될지 학생 눈높이에 맞춰 친절하게 설명해주세요.
    """

    user_prompt = f"""
    [사용자 질문]
    {user_query}

    [동아리 정보]
    {full_text}
    """

    # 7️⃣ GPT 호출
    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.5,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        description = resp.choices[0].message.content
    except Exception as e:
        description = f"❗ GPT 응답 중 오류 발생: {str(e)}"

    # 8️⃣ 결과 반환
    result = {
        "추천_동아리_doc_id": best_doc_id,
        "유사도": best_sim,
        "동아리_내용": full_text,
        "LLM_설명": description
    }

    return result


# ============================================
# 🔹 실행 예시
# ============================================
if __name__ == "__main__":
    query = "창업 관련 동아리를 알고 싶어요"
    print(f"\n[사용자 입력] {query}\n")

    rec = recommend_and_describe_club(query)

    if isinstance(rec, str):
        print(rec)
    else:
        print(f"🎯 추천 동아리 (doc_id={rec['추천_동아리_doc_id']}, 유사도={rec['유사도']})\n")
        print("📘 동아리 정보:\n", rec["동아리_내용"])
        print("\n💬 LLM 설명:\n", rec["LLM_설명"])
