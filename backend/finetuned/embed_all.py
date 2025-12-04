"""
전체 청크 임베딩 → embeddings 테이블 저장
테이블 구조:
    chunk_id INT
    embedding VECTOR(768)
    model_name TEXT
    created_at TIMESTAMP
"""

import psycopg2
from sentence_transformers import SentenceTransformer
from datetime import datetime
from tqdm import tqdm


# ===============================
# 1. PostgreSQL 연결
# ===============================
print("🔌 Connecting to PostgreSQL...")
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    dbname="kwchatbot_lec",
    user="postgres",
    password="3864"
)
cur = conn.cursor()
print(" Connected!")


# ===============================
# 2. 파인튜닝 모델 불러오기
# ===============================
MODEL_PATH = r"C:/Users/ols11/KW-DreamPath/backend/finetuned/triplet_finetuned_model"
print(" Loading model...")
model = SentenceTransformer(MODEL_PATH)
print(" Model loaded")


# ===============================
# 3. 아직 임베딩 안된 chunk 불러오기
# ===============================
print(" Loading chunks from doc_chunks...")

cur.execute("""
    SELECT chunk_id, chunk_text
    FROM doc_chunks
    WHERE chunk_id NOT IN (
        SELECT chunk_id FROM embeddings
    )
    ORDER BY chunk_id
""")
rows = cur.fetchall()

print(f" {len(rows)} chunks to embed")


# ===============================
# 4. 임베딩 생성 + DB 저장
# ===============================
print(" Embedding & inserting into DB...")

insert_sql = """
    INSERT INTO embeddings (chunk_id, embedding, model_name, created_at)
    VALUES (%s, %s, %s, %s)
"""

for chunk_id, chunk_text in tqdm(rows, desc="Embedding"):
    emb = model.encode(chunk_text).tolist()  # numpy → python list

    cur.execute(insert_sql, (
        chunk_id,
        emb,
        "triplet_finetuned_model",
        datetime.now()
    ))

conn.commit()
cur.close()
conn.close()

print(" All embeddings saved into DB!")
