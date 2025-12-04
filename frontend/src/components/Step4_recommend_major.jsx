import React from "react";
import kw_circle from "../assets/kw_circle.png"; 

function Step4_recommend_major({ majors, loading }) {
  const hasData = majors && (
    (majors.double_major?.length > 0) || 
    (majors.deep_major?.length > 0) ||
    (majors.micro_major?.length > 0)
  );

  return (
    // [수정] w-8/12 -> w-full
    <div className="w-full bg-white p-6 shadow-md rounded-xl border border-gray-100 font-sans">
      <div className="flex items-center space-x-3 mb-4">
        <img src={kw_circle} onError={(e)=>e.target.style.display='none'} alt="icon" className="w-6 h-6 opacity-80" />
        <h2 className="text-lg font-bold text-gray-800">다전공 추천 로드맵</h2>
      </div>

      {loading ? (
        <div className="text-center py-8 text-gray-400 animate-pulse">다전공 분석 중...</div>
      ) : hasData ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="bg-blue-50 p-3 rounded-lg border border-blue-100">
            <h3 className="font-bold text-blue-800 text-sm mb-2">🔗 복수전공</h3>
            <ul className="text-xs text-gray-700 space-y-1">
              {majors?.double_major?.map((m, i) => <li key={i}>• {m}</li>)}
            </ul>
          </div>
          <div className="bg-red-50 p-3 rounded-lg border border-red-100">
            <h3 className="font-bold text-[#840E1E] text-sm mb-2">🔥 심화전공</h3>
            <ul className="text-xs text-gray-700 space-y-1">
              {majors?.deep_major?.map((m, i) => <li key={i}>• {m}</li>)}
            </ul>
          </div>
          <div className="bg-green-50 p-3 rounded-lg border border-green-100">
            <h3 className="font-bold text-green-800 text-sm mb-2">🧩 마이크로</h3>
            <ul className="text-xs text-gray-700 space-y-1">
              {majors?.micro_major?.map((m, i) => <li key={i}>• {m}</li>)}
            </ul>
          </div>
        </div>
      ) : (
        <div className="text-center text-gray-400 py-6 text-sm">추천 다전공 정보가 표시됩니다.</div>
      )}
    </div>
  );
}

export default Step4_recommend_major;