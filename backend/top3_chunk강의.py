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
    "password": "kk003300kk*"
}

# ===== SBERT 모델 =====

MODEL_PATH = "triplet_finetuned_model"
model = SentenceTransformer(MODEL_PATH)



# ============================================
# 1️⃣ Weighted document scoring 기반 검색
# ============================================
def fetch_ranked_documents(query_embedding, db_categories):

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

    ranked_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
    top_docs = [doc_id for doc_id, _ in ranked_docs[:3]]

    return [(doc_id, doc_chunks[doc_id]) for doc_id in top_docs]


# ============================================
# 2️⃣ 문서 전체 조립
# ============================================
def build_full_document(doc_id, chunk_list):

    chunk_list_sorted = sorted(chunk_list, key=lambda x: x["chunk_index"])
    full_text = "\n".join(c["text"] for c in chunk_list_sorted)
    metadata = chunk_list_sorted[0]["metadata"] if chunk_list_sorted else {}

    return full_text, metadata


# ============================================
# 3️⃣ LLM RAG 생성 (전달된 context 출력)
# ============================================
def generate_llm_answer(user_query, docs):

    context_items = []

    for doc_id, chunk_list in docs:
        full_text, metadata = build_full_document(doc_id, chunk_list)
        meta_str = json.dumps(metadata, ensure_ascii=False, indent=2)

        context_items.append(
            f"[ 문서 ID: {doc_id} ]\n"
            f"-----\n본문:\n{full_text}\n\n메타데이터:\n{meta_str}\n"
        )

    context = "\n".join(context_items)

    # 🔥 LLM에게 보낸 내용 직접 출력
    print("\n========== 📤 LLM에 전달된 CONTEXT ==========\n")
    print(context)
    print("==============================================\n")

    system_msg = """
당신은 광운대학교 KW Chatbot입니다.
아래 CONTEXT에 기반하여 정확하고 간결하게 답변하세요.
"""

    user_msg = f"{context}\n\n질문: {user_query}\n\n정답:"

    # 🔥 프롬프트 전체 출력
    print("========== 📤 LLM 최종 PROMPT ==========\n")
    print("SYSTEM:", system_msg)
    print("\nUSER:", user_msg)
    print("==========================================\n")

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
# 4️⃣ 실행 + 출력
# ============================================
def print_docs_and_llm(category_key, user_query):

    query_emb = model.encode(user_query).tolist()
    ranked_docs = fetch_ranked_documents(query_emb, [category_key])

    if not ranked_docs:
        print("❗ 관련 문서 없음")
        return

    print("\n========== 🔍 Top 문서 (doc_id 기준) ==========")
    for doc_id, chunks in ranked_docs:
        print(f"\n▶ doc_id={doc_id} (총 {len(chunks)} 청크)")
        for c in chunks:
            print(f" - chunk_id: {c['chunk_id']}  sim={c['similarity']:.3f}  weighted={c['weighted_sim']:.3f}")

    print("\n========================================================\n")

    llm_ans = generate_llm_answer(user_query, ranked_docs)

    print("\n================ 💬 LLM 최종 답변 ================\n")
    print(llm_ans)
    print("\n==================================================\n")


# ============================================
# 실행 예시
# ============================================
if __name__ == "__main__":
    category = "강의정보"
    query = "인공지능 관련 강의 알려줘"

    print_docs_and_llm(category, query)
