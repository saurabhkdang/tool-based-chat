import React, {useState, useEffect, useRef} from "react";
import axios from 'axios';
import './App.css';

function App(){
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({behavior: "smooth"});
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async(e) => {
    e.preventDefault();
    if(!input.trim()) return;

    const userMessage = {role: 'user', content: input};
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const history = messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      const response = await axios.post('http://127.0.0.1:8000/chat', {
        message: input,
        history: history
      });

      const aiMessage = {role: 'assistant', content: response.data.response};
      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error("Error calling AI Agent: ",error);
      setMessages((prev) => [...prev, { role: 'assistant', content: "Sorry, I'm having trouble connecting to my brain. Please check if the backend is running." }]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="chat-container">
      <header className="chat-header">
        <h1>AI Employee Agent</h1>
        <p>Ask me about your employees</p>
      </header>

      <div className="messages-list">
        {messages.length === 0 && (
          <div className="welcome-screen">
            <div className="bot-icon">🤖</div>
            <p>Hello! I can help you manage employee data. Try asking "Who are the employees?" or "Tell me about employee 1".</p>
          </div>
        )}
        {messages.map((msg, index) => (
          <div key={index} className={`message-wrapper ${msg.role}`}>
            <div className="message-bubble">
              {msg.content}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message-wrapper assistant">
            <div className="message-bubble loading">
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="dot"></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="input-area" onSubmit={sendMessage}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message here..."
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}

export default App;