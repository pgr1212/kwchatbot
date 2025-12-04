import os
import json
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from openai import OpenAI

# ===== .env 불러오기 =====
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# ===== DB 설정 =====
PG_DSN = {
    "host": "localhost",
    "dbname": "kwchatbot_lec",
    "user": "postgres",
    "password": "3864"
}

# ===== SBERT 모델 =====
MODEL_PATH = "triplet_finetuned_model"
model = SentenceTransformer(MODEL_PATH)

# ============================================
# 🔹 카테고리 매핑
# ============================================
category_map = {
    "강의": ["강의정보", "학과정보"],
    "동아리": ["동아리"],
    "내일배움": ["내일배움"],
    "직업정보": ["직업정보"],
    "학부연구생": ["연구실 정보"]
}


# ============================================
# 🔹 1️⃣ 특정 카테고리 내에서 top3 유사 청크 검색
# ============================================
def fetch_top3_chunks(query_embedding, db_categories):
    conn = psycopg2.connect(**PG_DSN)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT 
            dc.chunk_id,
            dc.doc_id,
            dc.chunk_index,
            dc.chunk_text,
            dc.category,
            dc.chunk_metadata,
            1 - (e.embedding <#> %s::vector) AS similarity
        FROM embeddings e
        JOIN doc_chunks dc ON e.chunk_id = dc.chunk_id
        WHERE dc.category = ANY(%s)
        ORDER BY e.embedding <#> %s::vector
        LIMIT 3;
        """,
        (query_embedding, db_categories, query_embedding)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# ============================================
# 🔹 2️⃣ LLM 답변 생성 (RAG)
# ============================================
def generate_llm_answer(user_query, chunks):
    context_items = []

    for text, meta in chunks:
        meta_str = json.dumps(meta, ensure_ascii=False)
        context_items.append(
            f"-----\n본문:\n{text}\n\n메타데이터:\n{meta_str}"
        )

    context = "\n".join(context_items)

    system_msg = """
당신은 광운대학교 KW Chatbot입니다.
아래 제공된 CONTEXT 정보만 기반으로 사용자가 알기쉽게 친절하게 답변하세요.
교수명도 필요하면 같이 대답하세요.

"""

    user_msg = f"{context}\n\n질문: {user_query}\n\n정답:"

    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.0,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
        )
        return resp.choices[0].message.content
    
    except Exception as e:
        return f"[LLM 오류] {str(e)}"


# ============================================
# 🔹 3️⃣ Top-3 청크 출력 + LLM 답변
# ============================================
def print_top3_and_llm(category_key, user_query):
    if category_key not in category_map:
        print("❌ 존재하지 않는 카테고리입니다.")
        return

    db_categories = category_map[category_key]
    query_embedding = model.encode(user_query).tolist()

    rows = fetch_top3_chunks(query_embedding, db_categories)

    if not rows:
        print("❗ 유사한 청크 없음")
        return

    # 프롬프트용 context 준비
    llm_chunks = []

    print(f"\n========== 🔍 Top-3 유사 청크 (카테고리: {category_key}) ==========")
    for i, row in enumerate(rows, start=1):
        chunk_id, doc_id, idx, text, category, metadata, sim = row

        print(f"\n[{i}] ▶ 카테고리: {category}")
        print(f"   ▸ doc_id: {doc_id}")
        print(f"   ▸ chunk_id: {chunk_id}, index: {idx}")
        print(f"   ▸ similarity: {round(float(sim), 4)}")

        print("\n📄 전체 텍스트:")
        print(text)

        print("\n🗂 메타데이터:")
        print(json.dumps(metadata, ensure_ascii=False, indent=4))
        print("-" * 60)

        # LLM에 넘길 context 구성
        llm_chunks.append((text, metadata))

    print("\n========================================================\n")

    # 🔥 LLM 답변 생성
    llm_answer = generate_llm_answer(user_query, llm_chunks)

    print("\n================ 💬 LLM 최종 답변 ================\n")
    print(llm_answer)
    print("\n==================================================\n")


# ============================================
# 🔹 4️⃣ 실행
# ============================================
if __name__ == "__main__":
    category_input = "강의정보"
    query = "인공지능 관련 강의 알려줘 "

    print_top3_and_llm(category_input, query)
