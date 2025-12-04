import psycopg2
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os

load_dotenv()

# DB 연결 정보
PG_DSN = {
    "host": "localhost",
    "port": "5432",
    "dbname": "kwchatbot",
    "user": "postgres",
    "password": "3864", 
}

# 모델 로드
MODEL_PATH = "jhgan/ko-sbert-sts"
model = SentenceTransformer(MODEL_PATH)

def recommend_major_ai(current_major: str, career_interest: str, top_k=15):
    """
    진로(career_interest)와 관련된 '강의'를 찾고, 
    해당 강의가 개설된 '학과'를 추출하여 다전공을 추천합니다.
    (recommend_lecture.py의 데이터 및 로직 활용)
    """
    # 1. 진로 키워드 임베딩
    query_embedding = model.encode(career_interest).tolist()

    conn = psycopg2.connect(**PG_DSN)
    cur = conn.cursor()

    # 2. '강의정보' 카테고리에서 유사한 강의 검색 (top_k를 넉넉하게 잡음)
    # recommend_lecture.py와 동일한 데이터 소스 사용
    sql = """
        SELECT dc.chunk_text, 1 - (e.embedding <#> %s::vector) AS similarity
        FROM embeddings e
        JOIN doc_chunks dc ON e.chunk_id = dc.chunk_id
        WHERE dc.category = '강의정보'
        ORDER BY e.embedding <#> %s::vector
        LIMIT %s;
    """
    
    cur.execute(sql, (query_embedding, query_embedding, top_k))
    rows = cur.fetchall()
    
    cur.close()
    conn.close()

    # [수정] 심화전공은 무조건 '사용자 입력 전공 + (심화)' 형태로 고정
    results = {
        "double_major": [], 
        "deep_major": [f"{current_major} (심화)"],   
        "micro_major": []   
    }

    # 중복 제거를 위한 세트
    seen_majors = set()

    for row in rows:
        text_content = row[0]
        department = "학과 정보 없음"

        # 3. 텍스트에서 '학과명' 추출 (recommend_lecture.py의 파싱 로직 적용)
        lines = text_content.strip().split("\n")
        for line in lines:
            if "학과명" in line or "개설학과" in line or "소속학과" in line:
                if ":" in line:
                    department = line.split(":", 1)[1].strip()
                    break # 학과를 찾으면 루프 중단
        
        # 유효하지 않은 학과명 필터링
        if department in ["학과 정보 없음", "", "교양", "교양학부"]:
            continue
            
        # 이미 추가된 학과면 건너뜀
        if department in seen_majors:
            continue
            
        seen_majors.add(department)

        # 4. 분류 로직
        # 본전공명 공백 제거 비교 (ex: "소프트웨어 학부" == "소프트웨어학부")
        clean_current = current_major.replace(" ", "")
        clean_target = department.replace(" ", "")

        # [수정] 본전공과 일치하는 학과가 나오면, 이미 deep_major에 추가했으므로 넘어갑니다.
        if clean_current in clean_target:
            continue

        if "트랙" in department or "마이크로" in department:
            results["micro_major"].append(department)
        
        else:
            # 그 외는 복수전공으로 추천
            results["double_major"].append(department)

    # 결과가 너무 많으면 상위 3개씩만 자르기 (선택 사항)
    results["double_major"] = results["double_major"][:3]
    # results["deep_major"]는 이미 1개로 고정되어 있으므로 슬라이싱 불필요
    results["micro_major"] = results["micro_major"][:3]

    return results