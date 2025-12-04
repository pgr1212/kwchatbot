// src/components/SearchBar.jsx
import React from "react";

export default function SearchBar({ value, onChange, onSubmit }) {
  return (
    <div className="w-full flex justify-center">
      <form 
        onSubmit={onSubmit} 
        className="w-full flex items-center bg-white border-2 border-gray-300 rounded-lg shadow-sm h-[48px]"
      >
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="어떤 직종 및 직업이 궁금하신가요?"
          className="flex-1 px-4 text-gray-700 placeholder-gray-400 outline-none"
        />

        <button 
          type="submit" 
          className="px-4 text-gray-600"
        >
          🔍
        </button>
      </form>
    </div>
  );
}
