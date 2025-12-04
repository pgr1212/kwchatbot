import psycopg2
import json
from psycopg2 import sql

# ------------------ DB 연결 ------------------
try:
    conn = psycopg2.connect(
        host="localhost",
        dbname="kwchatbot",   # ✅ 대문자 K 주의
        user="postgres",
        password="3864"  # ✅ 네 비밀번호
    )
    cur = conn.cursor()
    print(" DB 연결 성공: KW chatbot")

except Exception as e:
    print(" DB 연결 실패:", e)
    exit()


# ------------------ 기존 데이터 비우기 (선택) ------------------
try:
    print("🧹 기존 데이터 비우는 중...")
    cur.execute("""
        TRUNCATE TABLE embeddings, doc_chunks, doc_categories, doc_status, raw_doc CASCADE;
    """)
    conn.commit()
    print(" 기존 데이터 초기화 완료.\n")
except Exception as e:
    print(" 초기화 중 오류 발생 (무시 가능):", e)
    conn.rollback()


# ------------------ ID 시작값 ------------------
doc_id_counter = 1
chunk_id_counter = 1
embedding_id_counter = 1


# ------------------ JSON 파일 경로 ------------------
file_path = r"C:\Users\ols11\KW-DreamPath\backend\최종_통합_DB.json"  # ✅ 네 실제 경로

# 파일 열기
try:
    f = open(file_path, "r", encoding="utf-8")
    print(f" JSON 파일 열기 성공 → {file_path}\n")
except FileNotFoundError:
    print(" JSON 파일을 찾을 수 없습니다. 경로를 확인하세요.")
    exit()


# ------------------ 데이터 삽입 ------------------
inserted_docs = 0

for line in f:
    if not line.strip():
        continue  # 빈 줄 건너뜀

    doc = json.loads(line)

    try:
        # 새로운 doc_id
        new_doc_id = doc_id_counter
        doc_id_counter += 1

        # 1️⃣ raw_doc
        cur.execute("""
            INSERT INTO raw_doc (doc_id, source_type, source_file, row_data, raw_created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            new_doc_id,
            doc.get("source_type"),
            doc.get("source_file"),
            json.dumps(doc.get("row_data"), ensure_ascii=False),
            doc.get("raw_created_at")
        ))

        # 2️⃣ doc_status
        status = doc.get("doc_status", {})
        cur.execute("""
            INSERT INTO doc_status (doc_id, is_chunked, is_embedded, chunked_at, embedded_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            new_doc_id,
            status.get("is_chunked"),
            status.get("is_embedded"),
            status.get("chunked_at"),
            status.get("embedded_at")
        ))

        # 3️⃣ doc_categories
        for category in doc.get("doc_categories", []):
            cur.execute("""
                INSERT INTO doc_categories (doc_id, category)
                VALUES (%s, %s)
            """, (new_doc_id, category))

        # 4️⃣ doc_chunks + 5️⃣ embeddings
        for chunk in doc.get("doc_chunks", []):
            new_chunk_id = chunk_id_counter
            chunk_id_counter += 1

            cur.execute("""
                INSERT INTO doc_chunks (chunk_id, doc_id, chunk_index, chunk_text, chunk_metadata, category)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                new_chunk_id,
                new_doc_id,
                chunk.get("chunk_index"),
                chunk.get("chunk_text"),
                json.dumps(chunk.get("chunk_metadata"), ensure_ascii=False),
                chunk.get("category")
            ))

            emb = chunk.get("embedding")
            if emb:
                new_embedding_id = embedding_id_counter
                embedding_id_counter += 1

                cur.execute("""
                    INSERT INTO embeddings (embedding_id, chunk_id, embedding, model_name, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    new_embedding_id,
                    new_chunk_id,
                    emb.get("embedding"),
                    emb.get("model_name"),
                    emb.get("created_at")
                ))

        inserted_docs += 1
        if inserted_docs % 50 == 0:
            conn.commit()
            print(f" {inserted_docs}개 문서까지 저장 완료...")

    except Exception as e:
        print(f" 문서 {new_doc_id} 삽입 중 오류 발생:", e)
        conn.rollback()


# ------------------ 마무리 ------------------
conn.commit()
cur.close()
conn.close()
f.close()

print(f"\n 통합본 삽입 완료!")
print(f"총 {inserted_docs}개 문서가 KWchatbot DB에 추가되었습니다.")
