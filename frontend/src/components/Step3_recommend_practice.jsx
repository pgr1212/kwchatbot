import React, { useState } from "react";
import step3_tree from "../assets/step3_tree.png";
import mascot from "../assets/mascot.png";

function TrainingDetailModal({ training, onClose }) {
  if (!training) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg p-8">
        <h3 className="text-xl font-bold text-[#840E1E] mb-4">{training.title}</h3>
        <p className="text-gray-600 mb-2">{training.subtitle}</p>
        <p className="text-gray-500 text-sm mb-4">{training.address}</p>
        <div className="bg-gray-50 p-3 rounded text-sm mb-4">{training.detail}</div>
        <button onClick={onClose} className="w-full py-2 bg-[#840E1E] text-white rounded-lg">닫기</button>
      </div>
    </div>
  );
}

function Step3_recommend_practice({ trainings, loading }) {
  const [selectedTraining, setSelectedTraining] = useState(null);

  return (
    // [수정] w-8/12 -> w-full
    <div className="w-full bg-white p-6 shadow-md rounded-xl border border-gray-100 font-sans">
      <div className="flex items-center space-x-3 mb-4">
        <img src={step3_tree} onError={(e)=>e.target.src=mascot} alt="icon" className="w-6 h-6" /> 
        <h2 className="text-lg font-bold text-gray-800">국비지원 교육과정</h2>
      </div>

      {loading ? (
        <div className="text-center py-8 text-gray-400 animate-pulse">교육과정 검색 중...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {trainings && trainings.length > 0 ? (
            trainings.map((item, index) => (
              <div key={index} onClick={() => setSelectedTraining(item)} className="border border-gray-200 rounded-lg p-3 hover:border-[#840E1E] cursor-pointer bg-gray-50">
                <p className="font-bold text-gray-800 text-sm truncate">{item.title}</p>
                <p className="text-xs text-gray-500 mt-1">{item.subtitle}</p>
              </div>
            ))
          ) : (
             <div className="col-span-2 text-center text-gray-400 py-6 text-sm">교육과정 정보가 없습니다.</div>
          )}
        </div>
      )}
      <TrainingDetailModal training={selectedTraining} onClose={() => setSelectedTraining(null)} />
    </div>
  );
}

export default Step3_recommend_practice;