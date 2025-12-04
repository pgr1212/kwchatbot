// src/components/ChatBox.jsx
import React, { useState, useRef, useEffect } from "react";
import mascot from "../assets/mascot.png";
import sendIcon from "../assets/send.png";
import { sendQuestion } from "../api/request.jsx";

function ChatBox({ title }) {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "궁금한 점을 입력해주세요 :)" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  const handleSend = async () => {
    if (input.trim() === "") return;
    const newMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, newMessage]);
    const question = input;
    setInput("");
    setLoading(true);
    const answer = await sendQuestion(question, title);
    setMessages((prev) => [...prev, { sender: "bot", text: answer }]);
    setLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleSend();
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    // [수정] w-8/12 -> w-full 변경
    <div className="w-full h-[650px] bg-white rounded-b-[30px] shadow-none p-6 relative flex flex-col items-center">
      
      {/* 채팅 내용 영역 */}
      <div className="mt-2 w-full h-[480px] px-2 overflow-y-auto custom-scrollbar">
        {messages.map((msg, i) => (
          <div key={i} className={`flex mb-4 ${msg.sender === "bot" ? "justify-start" : "justify-end"}`}>
            {msg.sender === "bot" ? (
              <div className="flex items-start space-x-2">
                <div className="flex flex-col items-center justify-center min-w-[50px]">
                  <img src={mascot} alt="마스코트" className="w-[45px] object-contain" />
                  <p className="text-[10px] font-bold text-gray-600 mt-1">{title}</p>
                </div>
                <div className="bg-[#F4D2D2] text-gray-900 px-3 py-2 rounded-xl rounded-tl-none shadow-sm text-sm max-w-[200px] break-words">
                  {msg.text}
                </div>
              </div>
            ) : (
              <div className="bg-gray-100 text-gray-900 px-3 py-2 rounded-xl rounded-tr-none shadow-sm text-sm max-w-[200px] break-words">
                {msg.text}
              </div>
            )}
          </div>
        ))}
        {loading && <div className="text-xs text-gray-400 ml-12 mb-4">답변 작성 중...</div>}
        <div ref={chatEndRef} />
      </div>

      {/* 입력창 영역 */}
      <div className="absolute bottom-6 w-[90%] flex items-center h-[45px]">
        <div className="flex items-center w-full h-full border border-gray-300 rounded-full bg-gray-50 px-4 focus-within:border-[#840E1E] transition-colors">
          <input
            type="text"
            placeholder="질문 입력..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-grow outline-none text-sm bg-transparent"
          />
          <button onClick={handleSend} disabled={loading} className="ml-2 opacity-70 hover:opacity-100">
             <img src={sendIcon} alt="전송" className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default ChatBox;