import psycopg2
import json
import random

PG_DSN = {
    "host": "localhost",
    "dbname": "kwchatbot_lec",
    "user": "postgres",
    "password": "3864"
}

anchor_templates = [
    "{학과} 전공로드맵 알려줘.",
    "{학과} 로드맵 보여줘",
    "{학과}에 대해서 알려줘."
    "{학과} 전공 관련 강의 알려줘",
    "{학과} 전공과목이 뭐가 있어?",
    "{학과} 전공로드맵 사진 보여줘.",
    "{학과}는 무슨 공부를 해?",
    "나는 {학과}인데 전공로드맵이 뭐야?"
]

# 출력 JSONL
out_path = "major_triplet_dataset.jsonl"
f = open(out_path, "w", encoding="utf-8")

# DB 연결
conn = psycopg2.connect(**PG_DSN)
cur = conn.cursor()

# 🔥 1) 학과정보 청크 가져오기
cur.execute("""
    SELECT doc_id, chunk_text, chunk_index
    FROM doc_chunks
    WHERE category = '학과정보'
    ORDER BY doc_id, chunk_index
""")

rows = cur.fetchall()

# 🔥 2) doc_id 기준으로 chunk 병합
from collections import defaultdict
docs = defaultdict(list)

for doc_id, text, idx in rows:
    docs[doc_id].append(text)

# 🔥 3) 전체 문서 텍스트 생성
full_docs = {}  # doc_id → full_text
for doc_id, chunks in docs.items():
    full_text = " ".join(chunks)
    full_docs[doc_id] = full_text

# 🔥 4) 학과명, 단과대학 등을 추출하는 간단 파서
def parse_major_info(text):
    # 예: "단과대학: 자연과학대학\n학과: 수학과\n전공로드맵: URL"
    lines = text.split()
    college, major = None, None
    for i in range(len(lines)):
        if "단과대학:" in lines[i]:
            college = lines[i+1]
        if "학과:" in lines[i]:
            major = lines[i+1]
    return college, major


# 전체 doc 목록
doc_list = list(full_docs.items())  # [(doc_id, full_text), ...]

for doc_id, full_text in doc_list:

    college, major = parse_major_info(full_text)

    if not major:
        continue

    positive = full_text

    # negative 5개 (자기 자신 제외)
    other_docs = [(d, t) for d, t in doc_list if d != doc_id]
    negative_samples = random.sample(other_docs, 8)

    for tmpl in anchor_templates:
        anchor = tmpl.format(학과=major)

        # 5개의 negative로 5개의 Triplet 생성
        for neg_doc_id, neg_text in negative_samples:

            row = {
                "anchor": anchor,
                "positive": positive,
                "negative": neg_text
            }

            f.write(json.dumps(row, ensure_ascii=False) + "\n")

f.close()
cur.close()
conn.close()

print("🔥 JSONL 생성 완료!", out_path)
