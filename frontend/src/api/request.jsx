// src/api/request.jsx
import axios from "axios";

// ✅ FastAPI 서버 주소 (필요시 IP 수정)
const API_URL = "https://vinic-zenia-abatingly.ngrok-free.dev/rag";

/**
 * 🔹 공통 챗봇 질의 함수
 * @param {string} query 사용자가 입력한 질문
 * @param {string} category 카테고리 이름 (강의 / 동아리 / 취업 정보 등)
 * @returns {string} 챗봇 응답 텍스트
 */
export async function sendQuestion(query, category) {
  try {
    const response = await axios.post(API_URL, {
      query,
      category: [category], // 페이지 이름에 따라 자동 설정
    });

    return response.data.answer || "서버에서 응답이 없습니다.";
  } catch (error) {
    console.error("❌ 서버 연결 실패:", error);
    return "서버 연결에 실패했습니다. (백엔드 실행 중인지 확인해주세요)";
  }
}

/**
 * 🔹 단순 질의용 함수 (ChatPage 구조 대체용)
 * ChatBox가 아닌 단일 요청에도 사용 가능
 */
export async function askChatbot(question) {
  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: question }),
    });
    if (!res.ok) throw new Error("서버 연결 실패");
    const data = await res.json();
    return data.answer || "응답이 없습니다.";
  } catch (err) {
    console.error("❌ 에러:", err);
    return "서버 연결에 실패했습니다.";
  }
}

