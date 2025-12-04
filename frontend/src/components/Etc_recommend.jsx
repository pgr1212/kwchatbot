import React from "react";

function Etc_recommend({ jobs, loading }) {
  return (
    // [수정] w-8/12 -> w-full
    <div className="w-full bg-white p-6 shadow-md rounded-xl border border-gray-100 font-sans mb-10">
      <div className="flex items-center space-x-3 mb-4">
        <h2 className="text-lg font-bold text-gray-800">별첨. 관련 추천 직업</h2>
      </div>

      {loading ? (
        <div className="text-center py-4 text-gray-400 text-sm">직업 분석 중...</div>
      ) : (
        <div className="flex flex-wrap gap-2">
          {jobs && jobs.length > 0 ? (
            jobs.map((job, index) => (
              <span key={index} className="px-4 py-1 border border-[#840E1E] rounded-full text-[#840E1E] font-bold text-sm bg-red-50">
                {job.name}
              </span>
            ))
          ) : (
            <p className="text-gray-400 text-sm w-full text-center">결과 없음</p>
          )}
        </div>
      )}
    </div>
  );
}

export default Etc_recommend;