import psycopg2
import json
import random
import re
from collections import defaultdict

# ================================================
# DB 설정
# ================================================
PG_DSN = {
    "host": "localhost",
    "dbname": "kwchatbot_lec",
    "user": "postgres",
    "password": "3864"
}

OUTPUT_FILE = "lecture_triplet_dataset.jsonl"

# ================================================
# Anchor 템플릿 (3개)
# ================================================
ANCHOR_NAME = "{교과목명} 강의 정보 알려줘"
ANCHOR_KW1 = "{keyword} 관련 강의 알려줘"
ANCHOR_KW2 = "{keyword} 배우는 수업 뭐 있어?"

# ================================================
# 교과목명 기반 keyword 추출
# ================================================
def extract_keywords_from_course_name(course_name):
    """
    - 한글만 추출
    - 공백 split
    - 길이 1짜리 제외
    - 최대 2개 keyword 사용
    """
    # 예: "생활속의글로벌경제-GlobalEconomy" → "생활속의글로벌경제"
    name = re.sub(r"[^가-힣]", " ", course_name)

    # 한글 토큰 나누기
    tokens = re.findall(r"[가-힣]+", name)

    # 너무 짧은 단어 제거
    clean = [t for t in tokens if len(t) > 1]

    # 최대 2개까지만 keyword로 사용
    return clean[:2] if clean else ["기본주제"]

# ================================================
# JSONL 파일 열기
# ================================================
out = open(OUTPUT_FILE, "w", encoding="utf-8")

# ================================================
# DB 연결
# ================================================
conn = psycopg2.connect(**PG_DSN)
cur = conn.cursor()

# ================================================
# 강의 chunk 가져오기
# ================================================
cur.execute("""
    SELECT doc_id, chunk_index, chunk_text
    FROM doc_chunks
    WHERE category = '강의정보'
    ORDER BY doc_id, chunk_index;
""")

rows = cur.fetchall()

lecture_docs = defaultdict(list)

for doc_id, idx, text in rows:
    lecture_docs[doc_id].append((idx, text))

# ================================================
# chunk 병합 + 교과목명 + keyword 추출
# ================================================
full_texts = {}
course_names = {}
keywords_map = {}

for doc_id, chunks in lecture_docs.items():

    # 1) chunk 병합
    chunks_sorted = sorted(chunks, key=lambda x: x[0])
    full_text = " ".join(t for _, t in chunks_sorted)
    full_texts[doc_id] = full_text

    # 2) 교과목명 추출
    course_name = None
    for _, t in chunks:
        if "교과목명:" in t:
            try:
                course_name = t.split("교과목명:")[1].split()[0]
            except:
                pass
            break

    if not course_name:
        course_name = f"강의{doc_id}"

    course_names[doc_id] = course_name

    # 3) keyword = **교과목명 기반 only**
    kws = extract_keywords_from_course_name(course_name)
    keywords_map[doc_id] = kws

# ================================================
# Triplet 생성
# ================================================
doc_ids = list(full_texts.keys())

for doc_id in doc_ids:

    pos = full_texts[doc_id]
    cname = course_names[doc_id]
    kws = keywords_map[doc_id]

    # negative 3개 샘플링
    neg_ids = random.sample([d for d in doc_ids if d != doc_id], 3)

    # (1) 교과목명 anchor
    anchor_name = ANCHOR_NAME.format(교과목명=cname)
    for neg in neg_ids:
        out.write(json.dumps({
            "anchor": anchor_name,
            "positive": pos,
            "negative": full_texts[neg]
        }, ensure_ascii=False) + "\n")

    # (2) keyword anchor 2개 (교과목명 기반)
    for kw in kws[:2]:
        anchor_kw1 = ANCHOR_KW1.format(keyword=kw)
        anchor_kw2 = ANCHOR_KW2.format(keyword=kw)

        for neg in neg_ids:
            out.write(json.dumps({
                "anchor": anchor_kw1,
                "positive": pos,
                "negative": full_texts[neg]
            }, ensure_ascii=False) + "\n")

            out.write(json.dumps({
                "anchor": anchor_kw2,
                "positive": pos,
                "negative": full_texts[neg]
            }, ensure_ascii=False) + "\n")

# 종료
out.close()
conn.close()

print("🔥 강의 Triplet JSONL 생성 완료:", OUTPUT_FILE)
