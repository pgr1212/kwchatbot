# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from rag_pipeline import generate_answer

from recommend_lecture import recommend_courses
from recommend_club import recommend_one_club
from recommend_hakyeon import recommend_one_hakyeon
from recommend_job import recommend_jobs
from recommend_training import recommend_trainings
from recommend_major import recommend_major_ai

app = FastAPI()

# ===================================================
# CORS 설정 (외부 접속 허용)
# ===================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청 모델
class QueryRequest(BaseModel):
    query: str
    category: Optional[List[str]] = None
    department: Optional[str] = ""

@app.get("/")
def root():
    return {"message": "KW DreamPath Backend is Running!"}

@app.post("/rag")
def rag_handler(req: QueryRequest):
    result = generate_answer(req.query, req.category)
    return {"answer": result}

@app.get("/notice")
def notice_handler():
    result = generate_answer("공지사항 요청", category=["공지사항"])
    return {"answer": result}

@app.get("/status")
def status():
    return {"status": "✅ KW Chatbot backend running"}

# ===================================================
# 1단계: 강의 추천 (Top 4)
# ===================================================
@app.post("/recommend/lecture")
def recommend_lecture_handler(req: QueryRequest):
    results = recommend_courses(req.query, top_k=4)
    
    formatted_courses = []
    for item in results:
        formatted_courses.append({
            "title": item.get("title", "강의명 없음"),
            "department": item.get("department", "학과 정보 없음"),
            "professor": item.get("professor", "교수 정보 없음"),
            "detail": item.get("detail", "상세 내용 없음"),
            "similarity": item.get("similarity", 0)
        })
        
    return {"courses": formatted_courses}

# ===================================================
# 2단계: 동아리 추천 (Top 1)
# ===================================================
@app.post("/recommend/club")
def recommend_club_handler(req: QueryRequest):
    result = recommend_one_club(req.query)
    
    if not result or isinstance(result, str):
        return {"club": None}

    formatted_club = {
        "type": "동아리",
        "name": result.get("name", "동아리명 없음"),
        "field": result.get("field", "분야 정보 없음"),
        "affiliation": result.get("affiliation", "소속 정보 없음"),
        "introduction": result.get("introduction", "상세 내용 없음"),
        "professor": ""
    }
    return {"club": formatted_club}

# ===================================================
# 3단계: 학부연구생 추천 (Top 1)
# ===================================================
@app.post("/recommend/hakyeon")
def recommend_hakyeon_handler(req: QueryRequest):
    result = recommend_one_hakyeon(req.query)
    if isinstance(result, str) or result is None:
        return {"hakyeon": None}

    professor_name = result.get("professor", "교수 정보 없음")
    raw_field = result.get("field", "분야 정보 없음")
    if len(raw_field) > 15:  
        display_field = raw_field[:15] + "..." 
    else:
        display_field = raw_field

    full_text = result.get("introduction", "")

    formatted_hakyeon = {
        "type": "학부연구생",
        "name": result.get("name", "연구실명 없음"),
        "affiliation": f"{professor_name} 교수 연구실", 
        "field": display_field,
        "introduction": full_text, 
        "professor": professor_name 
    }
    return {"hakyeon": formatted_hakyeon}

# ===================================================
# 3단계: 훈련과정 추천 (Top 2)
# ===================================================
@app.post("/recommend/training")
def recommend_training_handler(req: QueryRequest):
    results = recommend_trainings(req.query, top_k=2)
    
    if isinstance(results, str) or not results:
        return {"training": []}

    formatted_list = []
    for item in results:
        formatted_list.append({
            "title": item.get("title", "과정명 없음"),
            "subtitle": item.get("subtitle", ""),
            "address": item.get("address", "주소 정보 없음"),
            "link": item.get("link", "#"),
            "detail": item.get("detail", "상세 내용이 없습니다.")
        })
        
    return {"training": formatted_list}

# ===================================================
# 별첨: 직업 추천 (Top 2)
# ===================================================
@app.post("/recommend/job")
def recommend_job_handler(req: QueryRequest):
    results = recommend_jobs(req.query, top_k=2)
    if isinstance(results, str) or not results:
        return {"jobs": []}

    formatted_list = []
    for item in results:
        formatted_list.append({
            "name": item.get("title", "직업명 없음"),
            "reason": item.get("요약", "")
        })
    return {"jobs": formatted_list}

# ===================================================
# [신규] 다전공 추천 (AI 기반)
# ===================================================
@app.post("/recommend/major")
def recommend_major_handler(req: QueryRequest):
    # 본전공 정보가 없으면 기본값 처리
    current_major = req.department if req.department else "전공미정"
    
    results = recommend_major_ai(current_major, req.query)
    return {"majors": results}