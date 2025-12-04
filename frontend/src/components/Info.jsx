import React, { useState } from "react";
import mascot from "../assets/mascot.png";

// 부모 컴포넌트(JobPage)로부터 검색 함수(onSearch)를 전달받습니다.
function Info({ onSearch }) {
  // 사용자의 입력값을 저장할 상태 변수
  const [query, setQuery] = useState("");
  const [department, setDepartment] = useState("");

  // 검색 버튼 클릭 시 실행될 함수
const handleSearch = () => {
    if (onSearch) {
      // 본전공 정보도 함께 전달
      onSearch(query, department); 
    }
  };

  // 엔터키 입력 시 실행될 함수
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="w-8/12 bg-white shadow-md font-sans">
      
      {/* 1. 마스코트 메시지 */}
      <div className="flex justify-start items-center pl-8 pr-16 pt-8 pb-4"> 
        <img src={mascot} alt="마스코트" className="w-[120px] h-[120px] object-contain flex-shrink-0 ml-[-20px]" />
        <div className="flex-1 ml-1"> 
          <div className="bg-red-100/70 border-l-4 border-[#840E1E] p-4 text-gray-800 text-[18px] rounded-lg shadow-sm">
            <p className="font-semibold">본인의 <span className="text-[#840E1E]">전공</span>과 <span className="text-[#840E1E]">진로</span>을 입력해주세요.</p>
            <p className="mt-1">맞춤형 진로 로드맵까지 설계해 드릴게요!</p>
          </div>
        </div>
      </div>
      
      {/* 2. 입력 필드 (본전공 + 관심직업) */}
      <div className="px-16 py-8 pt-0 flex space-x-4">
        
        {/* [추가] 본전공 입력창 */}
        <div className="w-1/3 relative border border-gray-300 rounded-lg overflow-hidden shadow-inner bg-gray-50">
           <input
            type="text"
            placeholder="본전공 (예: 정보융합학부)"
            className="w-full py-2 pl-4 pr-4 text-[18px] text-gray-700 focus:outline-none bg-transparent"
            value={department}
            onChange={(e) => setDepartment(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </div>

        {/* 관심 직업 입력창 */}
        <div className="w-2/3 relative border border-gray-300 rounded-lg overflow-hidden shadow-inner">
          <input
            type="text"
            placeholder="희망 진로/관심사 (예: 개발자, 인공지능)"
            className="w-full py-2 pl-4 pr-12 text-[18px] text-gray-700 focus:outline-none"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            onClick={handleSearch}
            className="absolute right-0 top-0 h-full w-12 flex items-center justify-center text-gray-500 hover:text-[#840E1E] transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </button>
        </div>

      </div>
    </div>
  );
}

export default Info;