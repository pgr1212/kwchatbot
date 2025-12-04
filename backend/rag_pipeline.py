import os
import json
import psycopg2
import numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

# ===== .env 불러오기 =====
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ===== 기본 설정 =====
OPENAI_MODEL = "gpt-3.5-turbo"  # 필요 시 gpt-4o 등으로 변경 가능
PG_DSN = {
    "host": "localhost",
    "dbname": "kwchatbot",  #  DB 이름
    "user": "postgres",
    "password": "3864",  #  비밀번호
}
SIM_THRESHOLD = 0.25  # 코사인 유사도 임계값 (낮을수록 더 많은 결과 허용)

# ===== SentenceTransformer (공개 한국어 SBERT 모델) =====
MODEL_PATH = "jhgan/ko-sbert-sts"
model = SentenceTransformer(MODEL_PATH)

# ===== OpenAI 클라이언트 =====
client = OpenAI(api_key=OPENAI_API_KEY)


# ==========================================
# 🔹 Postgres에서 top-3 유사 청크 가져오기
# ==========================================
def _fetch_top3_chunks(query_embedding, categories):
    conn = psycopg2.connect(**PG_DSN)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT dc.chunk_text, dc.chunk_metadata
        FROM embeddings e
        JOIN doc_chunks dc ON e.chunk_id = dc.chunk_id
        WHERE dc.chunk_metadata->>'카테고리' = ANY(%s)
        ORDER BY e.embedding <#> %s::vector
        LIMIT 3
        """,
        (categories, query_embedding),
    )
    cur.execute(
        """
        SELECT dc.chunk_text, dc.chunk_metadata
        FROM embeddings e
        JOIN doc_chunks dc ON e.chunk_id = dc.chunk_id
        WHERE dc.chunk_metadata->>'카테고리' = ANY(%s)
        ORDER BY e.embedding <#> %s::vector
        LIMIT 3
        """,
        (categories, query_embedding),
    )

    rows = cur.fetchall()

    #  검색된 청크를 콘솔에 출력
    #  검색된 청크를 콘솔에 출력
    print("\n========== 🔍 검색된 Top-3 청크 ==========")
    if not rows:
        print("검색 결과가 없습니다.")
        print("검색 결과가 없습니다.")
    else:
        for i, (text, meta) in enumerate(rows, 1):
            category_name = (
                meta.get("카테고리", "없음") if isinstance(meta, dict) else "없음"
            )
            preview = text[:200].replace("\n", " ")  # 줄바꿈 제거 + 일부만 출력
            print(f"[{i}] 카테고리: {category_name}")
            print(f"본문 미리보기: {preview}...\n")
    print("=========================================\n")

    cur.close()
    conn.close()
    return rows


# ==========================================
# 🔹 핵심: RAG 답변 생성 함수
# ==========================================
def generate_answer(user_query, category=None):
    # 사용자 질문 임베딩 생성
    query_embedding = model.encode(user_query).tolist()

    # 프론트엔드에서 받은 카테고리 이름 정리
    selected_category = None
    if category and isinstance(category, list):
        selected_category = category[0]

    # 버튼 이름 → DB 카테고리 매핑
    category_map = {
        "강의": ["강의정보", "학과정보"],
        "동아리": ["동아리"],
        "취업 정보": ["취업"],
    }
    db_categories = category_map.get(selected_category, None)

    # DB에서 유사한 청크 top-3 검색
    rows = _fetch_top3_chunks(query_embedding, categories=db_categories)

    # 유사도 임계값 검사
    if not rows:
        return "관련 정보를 찾지 못했습니다."

    top_texts = [t for (t, _m) in rows]
    qvec = np.array(query_embedding).reshape(1, -1)
    cvecs = model.encode(top_texts)
    sims = cosine_similarity(qvec, cvecs)[0]

    if float(np.max(sims)) < SIM_THRESHOLD:
        return "해당 주제와 유사한 정보를 찾지 못했습니다."

    # 문맥(context) 구성
    context_items = []
    for i, (text, meta) in enumerate(rows, 1):
        meta_str = (
            json.dumps(meta, ensure_ascii=False) if not isinstance(meta, str) else meta
        )
        context_items.append(f"-----\n본문:\n{text}\n메타데이터:\n{meta_str}")
    context = "\n".join(context_items)

    # LLM 호출 - LLM이 더 잘 답변하도록 영어로 프롬프트 작성
    system = """
You are the KW University Chatbot.
Answer the user's question ONLY based on the provided CONTEXT.
If the answer is not explicitly found in the CONTEXT, respond:
"죄송합니다. 관련 정보를 찾지 못했습니다."
Do NOT use prior knowledge. Do NOT infer or guess.
Answer concisely and accurately in Korean.
"""

    user = f"""
CONTEXT:
{context}

USER QUESTION (in Korean):
{user_query}

INSTRUCTIONS:
1. Use only the content inside CONTEXT.
2. If information is missing, reply with:
   "죄송합니다. 관련 정보를 찾지 못했습니다."
3. Keep your answer clear and concise.
"""

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.0,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content

    except Exception as e:
        return f"LLM 응답 중 오류가 발생했습니다: {str(e)}"
