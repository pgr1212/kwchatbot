import psycopg2

# PostgreSQL 연결
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    dbname="KWchatbot",  # 통합 대상 DB
    user="postgres",
    password="kk003300kk*"
)
cur = conn.cursor()

# raw_doc 테이블의 마지막 doc_id 가져오기
cur.execute("SELECT MAX(doc_id) FROM raw_doc")
last_doc_id = cur.fetchone()[0]
if last_doc_id is None:
    last_doc_id = 0

# doc_chunks 테이블의 마지막 chunk_id 가져오기
cur.execute("SELECT MAX(chunk_id) FROM doc_chunks")
last_chunk_id = cur.fetchone()[0]
if last_chunk_id is None:
    last_chunk_id = 0

# embeddings 테이블의 마지막 embedding_id 가져오기
cur.execute("SELECT MAX(embedding_id) FROM embeddings")
last_embedding_id = cur.fetchone()[0]
if last_embedding_id is None:
    last_embedding_id = 0

print(f"📌 현재 마지막 doc_id: {last_doc_id}")
print(f"📌 현재 마지막 chunk_id: {last_chunk_id}")
print(f"📌 현재 마지막 embedding_id: {last_embedding_id}")

cur.close()
conn.close()
