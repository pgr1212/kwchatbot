import psycopg2
import json

# DB 연결 설정
conn = psycopg2.connect(
    host="localhost", dbname="KWchatbot", user="postgres", password="6578"
)
cur = conn.cursor()

# 시작 ID 값
doc_id_counter = 1
chunk_id_counter = 1
embedding_id_counter = 1

# JSONL 파일 열기
with open(r"C:\KW-DreamPath\backend\통합버전.json", "r", encoding="utf-8") as f:
    for line in f:
        doc = json.loads(line)

        # 새로운 doc_id
        new_doc_id = doc_id_counter
        doc_id_counter += 1

        # 1. raw_doc
        cur.execute(
            """
            INSERT INTO raw_doc (doc_id, source_type, source_file, row_data, raw_created_at)
            VALUES (%s, %s, %s, %s, %s)
        """,
            (
                new_doc_id,
                doc.get("source_type"),
                doc.get("source_file"),
                json.dumps(doc.get("row_data"), ensure_ascii=False),  # ✅ 여기를 수정!
                doc.get("raw_created_at"),
            ),
        )

        # 2. doc_status
        status = doc.get("doc_status", {})
        cur.execute(
            """
            INSERT INTO doc_status (doc_id, is_chunked, is_embedded, chunked_at, embedded_at)
            VALUES (%s, %s, %s, %s, %s)
        """,
            (
                new_doc_id,
                status.get("is_chunked"),
                status.get("is_embedded"),
                status.get("chunked_at"),
                status.get("embedded_at"),
            ),
        )

        # 3. doc_categories
        for category in doc.get("doc_categories", []):
            cur.execute(
                """
                INSERT INTO doc_categories (doc_id, category)
                VALUES (%s, %s)
            """,
                (new_doc_id, category),
            )

        # 4. doc_chunks + 5. embeddings
        for chunk in doc.get("doc_chunks", []):
            new_chunk_id = chunk_id_counter
            chunk_id_counter += 1

            cur.execute(
                """
                INSERT INTO doc_chunks (chunk_id, doc_id, chunk_index, chunk_text, chunk_metadata, category)
                VALUES (%s, %s, %s, %s, %s, %s)
            """,
                (
                    new_chunk_id,
                    new_doc_id,
                    chunk.get("chunk_index"),
                    chunk.get("chunk_text"),
                    json.dumps(chunk.get("chunk_metadata"), ensure_ascii=False),
                    chunk.get("category"),
                ),
            )

            emb = chunk.get("embedding")
            if emb:
                new_embedding_id = embedding_id_counter
                embedding_id_counter += 1

                cur.execute(
                    """
                    INSERT INTO embeddings (embedding_id, chunk_id, embedding, model_name, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                """,
                    (
                        new_embedding_id,
                        new_chunk_id,
                        emb.get("embedding"),
                        emb.get("model_name"),
                        emb.get("created_at"),
                    ),
                )

# 커밋 및 종료
conn.commit()
cur.close()
conn.close()
print(" 통합 삽입 완료 (ID 충돌 없음)")
