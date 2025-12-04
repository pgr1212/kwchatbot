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

# ===== 강의 전용 DB 설정 =====
PG_DSN = {
    "host": "localhost",
    "dbname": "kwchatbot",
    "user": "postgres",
    "password": "3864"
}

# ===== 파인튜닝된 SBERT 모델 로딩 =====
MODEL_PATH = "triplet_finetuned_model"
model = SentenceTransformer(MODEL_PATH)


# ============================================================
# 1️⃣ Weighted document scoring 기반 검색 (강의 전용)
# ============================================================
def _fetch_ranked_documents(query_embedding, db_categories):

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
        ORDER BY similarity DESC
        LIMIT 50;
        """,
        (query_embedding, db_categories)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        return []

    doc_scores = {}
    doc_chunks = {}

    for row in rows:
        chunk_id, doc_id, idx, text, category, metadata, sim = row

        if doc_id not in doc_scores:
            doc_scores[doc_id] = 0
            doc_chunks[doc_id] = []

        # 청크 위치 가중치
        weight = {0: 1.5, 1: 1.0, 2: 0.5}.get(idx, 1.0)

        doc_scores[doc_id] += float(sim) * weight

        doc_chunks[doc_id].append({
            "chunk_id": chunk_id,
            "chunk_index": idx,
            "text": text,
            "metadata": metadata,
            "similarity": float(sim),
            "weighted_sim": float(sim) * weight
        })

    # doc_id 기준 Top 문서 선택
    ranked_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
    top_docs = [doc_id for doc_id, _ in ranked_docs[:3]]

    return [(doc_id, doc_chunks[doc_id]) for doc_id in top_docs]


# ============================================================
# 2️⃣ 문서 전체 텍스트 조립
# ============================================================
def _build_full_document(doc_id, chunk_list):

    chunk_list_sorted = sorted(chunk_list, key=lambda x: x["chunk_index"])
    full_text = "\n".join(c["text"] for c in chunk_list_sorted)
    metadata = chunk_list_sorted[0]["metadata"] if chunk_list_sorted else {}

    return full_text, metadata


# ============================================================
# 3️⃣ LLM RAG 생성 → FastAPI에서 바로 불러 쓸 generate_answer()
# ============================================================
def generate_answer(user_query, category):

    # FastAPI에서 준 category는 항상 ["강의"] 또는 ["강의정보"]
    selected = category[0]

    # 강의 카테고리는 내부적으로 항상 2개 검색
    db_categories = ["강의정보", "학과정보"]

    query_emb = model.encode(user_query).tolist()

    # 문서 랭킹 
    ranked_docs = _fetch_ranked_documents(query_emb, db_categories)

    if not ranked_docs:
        return "관련 강의 정보를 찾지 못했습니다."

    # Context 생성
    context_items = []

    for doc_id, chunk_list in ranked_docs:
        full_text, metadata = _build_full_document(doc_id, chunk_list)
        meta_str = json.dumps(metadata, ensure_ascii=False, indent=2)

        context_items.append(
            f"[문서 ID: {doc_id}]\n"
            f"-----\n본문:\n{full_text}\n\n메타데이터:\n{meta_str}\n"
        )

    context = "\n".join(context_items)

    # LLM 프롬프트
    system_msg = """
You are the KW University Chatbot.
Answer the user's question ONLY based on the provided CONTEXT.
If the answer is not explicitly found in the CONTEXT, respond:
"죄송합니다. 관련 정보를 찾지 못했습니다."
Do NOT use prior knowledge. Do NOT infer or guess.
Answer concisely and accurately in Korean.
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
