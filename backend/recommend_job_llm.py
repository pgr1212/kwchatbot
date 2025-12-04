# ============================================
# 📚 SBERT 기반 직업 추천 + LLM 설명 시스템
#   - doc_chunks.category = '직업'
#   - 직업 여러 개(top_k) 추천 + GPT로 설명 생성
# ============================================

import os
import psycopg2
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv

# ===== .env 불러오기 =====
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ===== 기본 설정 =====
PG_DSN = {
    "host": "localhost",
    "dbname": "kwchatbot",
    "user": "postgres",
    "password": "3864"
}

SIM_THRESHOLD = 0.25  # 필요하면 조정

# ===== SBERT 모델 =====
MODEL_PATH = "jhgan/ko-sbert-sts"
model = SentenceTransformer(MODEL_PATH)

# ===== OpenAI 클라이언트 =====
client = OpenAI(api_key=OPENAI_API_KEY)


# ============================================
# 🔹 category='직업' 에서 유사 청크 검색
# ============================================
def _fetch_similar_job_chunks(query_embedding, top_k=3):
    """
    '직업' 카테고리에서 사용자 쿼리와 가장 유사한 청크 top_k개를 찾음
    """
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
        WHERE dc.category = '직업'
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
# 🔹 직업 추천 + LLM 설명
# ============================================
def recommend_jobs_with_llm(user_query, top_k=3):
    """
    사용자의 관심사(문장)를 입력받아,
    category='직업'에 해당하는 직업 정보를 top_k개 추천하고,
    추천 결과를 기반으로 GPT가 한글 설명을 생성한다.

    반환 예시:
    {
      "추천_직업_목록": [
        {"doc_id": 1, "title": "데이터 분석가", "요약": "...", "유사도": 0.83},
        ...
      ],
      "LLM_설명": "..."
    }
    """

    # 1️⃣ 사용자 쿼리 임베딩
    query_embedding = model.encode(user_query).tolist()

    # 2️⃣ 직업 청크 검색
    rows = _fetch_similar_job_chunks(query_embedding, top_k=top_k)

    if not rows:
        return "❗ 관련 직업 정보를 찾지 못했습니다."

    job_results = []
    for doc_id, chunk_id, chunk_text, category, sim in rows:
        sim = float(sim)
        if sim < SIM_THRESHOLD:
            continue

        title = chunk_text.splitlines()[0].strip()  # 첫 줄을 직업명으로 사용

        job_results.append({
            "doc_id": doc_id,
            "title": title,
            "요약": chunk_text,
            "유사도": round(sim, 4),
        })

    if not job_results:
        return "❗ 유사도 기준을 넘는 직업이 없습니다. (SIM_THRESHOLD 조정 필요)"

    # 3️⃣ LLM 프롬프트 구성
    system_prompt = """
    당신은 광운대학교 학생들을 위한 진로 상담 도우미입니다.
    아래 직업 목록은 학생의 관심사와 유사한 직업들입니다.
    각 직업이 어떤 일을 하는지, 어떤 역량이 필요한지,
    그리고 사용자의 질문과 어떻게 연결되는지
    대학생/취준생 눈높이에 맞춰 간단하고 친절하게 설명해 주세요.

    - 너무 길지 않게 정리하고
    - 각 직업별로 핵심 포인트 위주로 써 주세요.
    """

    jobs_text = "\n\n".join(
        [f"- {j['title']} (유사도: {j['유사도']})\n{j['요약']}" for j in job_results]
    )

    user_prompt = f"""
    [사용자 질문]
    {user_query}

    [추천 직업 목록]
    {jobs_text}
    """

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.5,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        explanation = resp.choices[0].message.content
    except Exception as e:
        explanation = f"❗ GPT 설명 생성 중 오류 발생: {str(e)}"

    return {
        "추천_직업_목록": job_results,
        "LLM_설명": explanation
    }


# ============================================
# 🔹 실행 예시
# ============================================
if __name__ == "__main__":
    query = "엑셀이나 데이터를 다루는 사무직 일을 하고 싶어요"
    from pprint import pprint

    rec = recommend_jobs_with_llm(query, top_k=3)
    print(f"[사용자 입력] {query}\n")
    pprint(rec)
