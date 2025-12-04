import React, { useState } from "react";
import step1_ground from "../assets/step1_ground.png";
import mascot from "../assets/mascot.png";

function CourseDetailModal({ course, onClose }) {
  if (!course) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg p-8">
        <h3 className="text-2xl font-bold text-[#840E1E] mb-4">{course.title}</h3>
        <p className="text-gray-700 mb-2"><b>학과:</b> {course.department}</p>
        <p className="text-gray-700 mb-4"><b>교수:</b> {course.professor}</p>
        <div className="bg-gray-50 p-3 rounded text-sm">{course.detail}</div>
        <button onClick={onClose} className="mt-6 w-full py-2 bg-[#840E1E] text-white rounded-lg">닫기</button>
      </div>
    </div>
  );
}

function CourseCard({ course, onClick }) {
    return (
        <div onClick={() => onClick(course)} className="bg-white border border-[#840E1E] rounded-lg p-4 shadow-sm hover:shadow-lg cursor-pointer min-h-[140px] flex flex-col justify-center relative">
            <p className="font-bold text-[#840E1E] truncate">{course.title}</p>
            <p className="text-xs text-gray-500 mt-1">{course.professor}</p>
            <img src={mascot} alt="icon" className="absolute bottom-1 right-2 w-6 opacity-50"/>
        </div>
    );
}

function Step1_recommend_lecture({ courses, loading }) {
  const [selectedCourse, setSelectedCourse] = useState(null);

  return (
    // [수정] w-8/12 -> w-full
    <div className="w-full bg-white p-6 shadow-md rounded-xl border border-gray-100 font-sans">
      <div className="flex items-center space-x-3 mb-4">
        <img src={step1_ground} alt="icon" className="w-6 h-6" /> 
        <h2 className="text-lg font-bold text-gray-800">추천 강의</h2>
      </div>

      {loading ? (
        <div className="text-center py-8 text-gray-400 animate-pulse">강의 분석 중...</div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {courses && courses.length > 0 ? (
            courses.map((course, index) => (
              <CourseCard key={index} course={course} onClick={setSelectedCourse} />
            ))
          ) : (
            <div className="col-span-4 text-center text-gray-400 py-6 text-sm">검색 결과가 여기에 표시됩니다.</div>
          )}
        </div>
      )}
      <CourseDetailModal course={selectedCourse} onClose={() => setSelectedCourse(null)} />
    </div>
  );
}

export default Step1_recommend_lecture;