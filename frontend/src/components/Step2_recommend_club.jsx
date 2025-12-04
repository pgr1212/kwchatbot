import React, { useState } from "react";
import step2_sprout from "../assets/step2_sprout.png"; 
import mascot from "../assets/mascot.png";

function ActivityDetailModal({ activity, onClose }) {
  if (!activity) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg p-8">
        <h3 className="text-2xl font-bold text-[#840E1E] mb-4">{activity.name}</h3>
        <p className="text-gray-700 mb-4">{activity.introduction}</p>
        <button onClick={onClose} className="w-full py-2 bg-[#840E1E] text-white rounded-lg">닫기</button>
      </div>
    </div>
  );
}

function ActivityCard({ activity, onClick, title }) {
    if (!activity) return <div className="flex-1 border border-gray-200 rounded-lg h-[120px] flex items-center justify-center text-gray-400 text-sm">정보 없음</div>;
    return (
        <div onClick={() => onClick(activity)} className="flex-1 bg-white border border-[#840E1E] rounded-lg p-4 shadow-sm hover:shadow-lg cursor-pointer h-[120px] flex flex-col justify-center relative">
            <p className="text-xs text-gray-500 mb-1">{title}</p>
            <p className="font-bold text-[#840E1E] text-lg truncate">{activity.name}</p>
            <p className="text-xs text-gray-400 truncate">{activity.field}</p>
            <img src={mascot} alt="icon" className="absolute bottom-1 right-2 w-6 opacity-50"/>
        </div>
    );
}

function Step2_recommend_club({ club, hakyeon, loading }) {
  const [selectedActivity, setSelectedActivity] = useState(null);

  return (
    // [수정] w-8/12 -> w-full
    <div className="w-full bg-white p-6 shadow-md rounded-xl border border-gray-100 font-sans">
      <div className="flex items-center space-x-3 mb-4">
        <img src={step2_sprout} alt="icon" className="w-6 h-6" /> 
        <h2 className="text-lg font-bold text-gray-800">동아리 및 학부연구생</h2>
      </div>
      
      {loading ? (
         <div className="text-center py-8 text-gray-400 animate-pulse">활동 분석 중...</div>
      ) : (
        <div className="flex gap-4">
            <ActivityCard activity={club} onClick={setSelectedActivity} title="추천 동아리" />
            <ActivityCard activity={hakyeon} onClick={setSelectedActivity} title="추천 연구실" />
        </div>
      )}
      <ActivityDetailModal activity={selectedActivity} onClose={() => setSelectedActivity(null)} />
    </div>
  );
}

export default Step2_recommend_club;