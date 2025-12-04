import React from "react";
import home from "../assets/home.png";
import kw_circle from "../assets/KWU.png";

function Header() {
  return (
    <div
      className="relative w-8/12 mt-[30px] bg-[#840E1E] text-white 
      py-[18px] text-[28px] font-bold flex justify-center items-center 
      space-x-[14px] shadow-md rounded-t-[35px] font-sans"
    >
      {/* 홈 버튼 */}
      <a
        href="/"
        className="absolute left-[4%] top-1/2 transform -translate-y-1/2 
        flex justify-center items-center w-[40px] h-[40px] 
        bg-white rounded-full shadow-md hover:scale-105 transition-transform"
      >
        <img src={home} alt="홈" className="w-6 h-6 cursor-pointer" />
      </a>

      {/* 중앙 로고 + 텍스트 */}
      <div className="flex justify-center items-center space-x-[14px]">
        <img src={kw_circle} alt="kw_circle" className="w-[60px] h-[60px]" />
        <span>광운대학교</span>
      </div>
    </div>
  );
}

export default Header;