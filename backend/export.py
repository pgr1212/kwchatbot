import psycopg2
import json

# DB 연결
conn = psycopg2.connect(
    host="localhost",
    dbname="KW_chatbot",
    user="postgres",
    password="비밀번호 입력",  # 🔒 여기에 본인 비번 넣기
)
cur = conn.cursor()

# 관계 유지한 JSON 생성 쿼리
query = """
SELECT json_build_object(
    'doc_id', r.doc_id,
    'source_type', r.source_type,
    'source_file', r.source_file,
    'row_data', r.row_data,
    'raw_created_at', r.raw_created_at,
    
    'doc_status', json_build_object(
        'is_chunked', s.is_chunked,
        'is_embedded', s.is_embedded,
        'chunked_at', s.chunked_at,
        'embedded_at', s.embedded_at
    ),
    
    'doc_categories', (
        SELECT json_agg(c.category)
        FROM doc_categories c
        WHERE c.doc_id = r.doc_id
    ),
    
    'doc_chunks', (
        SELECT json_agg(json_build_object(
            'chunk_index', ch.chunk_index,
            'chunk_text', ch.chunk_text,
            'chunk_metadata', ch.chunk_metadata,
            'category', ch.category,
            'embedding', (
                SELECT json_build_object(
                    'embedding', e.embedding,
                    'model_name', e.model_name,
                    'created_at', e.created_at
                )
                FROM embeddings e
                WHERE e.chunk_id = ch.chunk_id
                LIMIT 1
            )
        ))
        FROM doc_chunks ch
        WHERE ch.doc_id = r.doc_id
    )
)
FROM raw_doc r
LEFT JOIN doc_status s ON s.doc_id = r.doc_id;
"""

# 쿼리 실행 및 JSON 파일로 저장
cur.execute(query)
rows = cur.fetchall()

output_path = "C:/Users/kmins/KW_chatbot/data/동아리.json" # 원하는 경로로 수정
with open(output_path, "w", encoding="utf-8") as f:
    for row in rows:
        json.dump(row[0], f, ensure_ascii=False)
        f.write("\n")

cur.close()
conn.close()
print(f"✅ 관계 포함 JSON export 완료 → {output_path}")
