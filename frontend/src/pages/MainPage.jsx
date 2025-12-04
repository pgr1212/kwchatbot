// src/pages/MainPage.jsx
import React, { useState } from 'react';
import axios from 'axios';
import Header from "../components/Header";
import Info from "../components/Info";
import Step1_recommend_lecture from "../components/Step1_recommend_lecture";
import Step2_recommend_club from "../components/Step2_recommend_club";
import Step3_recommend_practice from "../components/Step3_recommend_practice";
import Step4_recommend_major from "../components/Step4_recommend_major"; 
import Etc_recommend from "../components/Etc_recommend";
import ChatBox from "../components/ChatBox";

const BACKEND_URL = "https://vinic-zenia-abatingly.ngrok-free.dev";

function MainPage() {
  const [loading, setLoading] = useState(false);
  
  // 데이터 상태 관리
  const [lectureData, setLectureData] = useState([]);
  const [clubData, setClubData] = useState(null);
  const [hakyeonData, setHakyeonData] = useState(null);
  const [trainingData, setTrainingData] = useState([]);
  const [majorData, setMajorData] = useState(null); 
  const [jobData, setJobData] = useState([]);

  // 챗봇 탭 상태
  const [activeChatTab, setActiveChatTab] = useState("lecture");

  // 검색 핸들러
  const handleSearch = async (query, department) => {
    if (!query || !query.trim()) {
      alert("희망하는 직업이나 진로를 입력해주세요!");
      return;
    }
    
    setLoading(true);
    
    try {
      const [lecRes, clubRes, hakRes, trainRes, majorRes, jobRes] = await Promise.all([
        axios.post(`${BACKEND_URL}/recommend/lecture`, { query: query, category: ["강의정보"] }),
        axios.post(`${BACKEND_URL}/recommend/club`, { query: query, category: ["동아리"] }),
        axios.post(`${BACKEND_URL}/recommend/hakyeon`, { query: query, category: ["학연생"] }),
        axios.post(`${BACKEND_URL}/recommend/training`, { query: query, category: ["내일배움"] }),
        axios.post(`${BACKEND_URL}/recommend/major`, { query: query, department: department || "정보융합학부" }), 
        axios.post(`${BACKEND_URL}/recommend/job`, { query: query, category: ["직업"] })
      ]);

      setLectureData(lecRes.data.courses || []);
      setClubData(clubRes.data.club || null);
      setHakyeonData(hakRes.data.hakyeon || null);
      setTrainingData(trainRes.data.training || []);
      setMajorData(majorRes.data.majors || null);
      setJobData(jobRes.data.jobs || []);

    } catch (error) {
      console.error("데이터 로딩 실패:", error);
      alert("추천 정보를 가져오는데 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center min-h-screen bg-gray-50 pb-20 font-sans">
      <Header /> 
      
      {/* 1. 검색창 (상단 고정) */}
      <Info onSearch={handleSearch} />
      
      {/* 2. 메인 컨텐츠 영역 (좌: 챗봇 / 우: 로드맵) */}
      <div className="w-8/12 mt-8 flex flex-col lg:flex-row gap-8 items-start">
        
        {/* [왼쪽] 챗봇 섹션 (스크롤 시 고정됨 - Sticky) */}
        <div className="w-full lg:w-[35%] flex-shrink-0 sticky top-10 self-start z-10">
          <div className="flex items-center space-x-1 mb-0">
            {[
              { id: "lecture", label: "강의 질문 🎓" },
              { id: "club", label: "동아리 질문 🤝" }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveChatTab(tab.id)}
                className={`flex-1 py-3 rounded-t-xl font-bold text-md transition-all duration-200 
                  ${activeChatTab === tab.id 
                    ? "bg-[#840E1E] text-white shadow-md translate-y-1 z-10" 
                    : "bg-gray-200 text-gray-500 hover:bg-gray-300"}`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="bg-white rounded-b-xl shadow-lg border-t-4 border-[#840E1E]">
              <div className={activeChatTab === "lecture" ? "block" : "hidden"}>
                  <ChatBox title="강의" />
              </div>
              <div className={activeChatTab === "club" ? "block" : "hidden"}>
                  <ChatBox title="동아리" />
              </div>
          </div>
          <p className="text-center text-gray-400 mt-3 text-xs">
            * 궁금한 점은 챗봇에게 바로 물어보세요!
          </p>
        </div>

        {/* [오른쪽] 진로 로드맵 추천 결과 (Step 1 ~ 4) */}
        <div className="w-full lg:flex-1 flex flex-col space-y-6">
          <Step1_recommend_lecture courses={lectureData} loading={loading} />
          <Step2_recommend_club club={clubData} hakyeon={hakyeonData} loading={loading} />
          <Step3_recommend_practice trainings={trainingData} loading={loading} />
          <Step4_recommend_major majors={majorData} loading={loading} />
          <Etc_recommend jobs={jobData} loading={loading} />
        </div>

      </div>
    </div>
  );
}

export default MainPage;