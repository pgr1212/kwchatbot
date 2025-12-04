from rag_pipeline import generate_answer

query = "광운대학교 컴퓨터정보공학부의 졸업 요건 알려줘"
answer = generate_answer(query)

print("🔹 답변:", answer)
