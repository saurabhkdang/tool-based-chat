import React, {useState, useEffect, useRef} from "react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './App.css';

const API_BASE = 'http://172.16.0.21:8000';

const markdownComponents = {
  table: ({ node, ...props }) => (
    <div className="table-wrapper"><table {...props} /></div>
  )
};

function App(){
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [moduleInfo, setModuleInfo] = useState({
    name: 'AI Assistant',
    subtitle: '',
    welcome_message: 'Hello! How can I help you today?'
  });
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({behavior: "smooth"});
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    fetch(`${API_BASE}/module-info`)
      .then((res) => res.json())
      .then((data) => setModuleInfo(data))
      .catch((error) => console.error("Error fetching module info: ", error));
  }, []);

  const appendToLastMessage = (chunk) => {
    setMessages((prev) => {
      const updated = [...prev];
      const lastIndex = updated.length - 1;
      updated[lastIndex] = {
        ...updated[lastIndex],
        content: updated[lastIndex].content + chunk
      };
      return updated;
    });
  };

  const sendMessage = async(e) => {
    e.preventDefault();
    if(!input.trim()) return;

    const userMessage = {role: 'user', content: input};
    const history = messages.map(msg => ({
      role: msg.role,
      content: msg.content
    }));

    setMessages((prev) => [...prev, userMessage, {role: 'assistant', content: ''}]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: userMessage.content, history})
      });

      if (!response.ok || !response.body) {
        throw new Error('Request failed');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;

      while (!done) {
        const {value, done: readerDone} = await reader.read();
        done = readerDone;
        if (value) {
          appendToLastMessage(decoder.decode(value, {stream: true}));
        }
      }
    } catch (error) {
      console.error("Error calling AI Agent: ",error);
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: 'assistant',
          content: "Sorry, I'm having trouble connecting to my brain. Please check if the backend is running."
        };
        return updated;
      });
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="chat-container">
      <header className="chat-header">
        <div className="header-avatar">🤖</div>
        <div>
          <h1>{moduleInfo.name}</h1>
          <p>{moduleInfo.subtitle}</p>
        </div>
      </header>

      <div className="messages-list">
        {messages.length === 0 && (
          <div className="welcome-screen">
            <div className="bot-icon">🤖</div>
            <p>{moduleInfo.welcome_message}</p>
          </div>
        )}
        {messages.map((msg, index) => (
          <div key={index} className={`message-wrapper ${msg.role}`}>
            {msg.role === 'assistant' && <div className="avatar bot-avatar">🤖</div>}
            <div className="message-bubble">
              {msg.role === 'assistant' ? (
                msg.content ? (
                  <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>{msg.content}</ReactMarkdown>
                ) : (
                  <span className="loading">
                    <span className="dot"></span>
                    <span className="dot"></span>
                    <span className="dot"></span>
                  </span>
                )
              ) : (
                msg.content
              )}
            </div>
            {msg.role === 'user' && <div className="avatar user-avatar">🙂</div>}
          </div>
        ))}
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
        <button type="submit" className="send-button" disabled={isLoading || !input.trim()} aria-label="Send message">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4 12L20 4L13 20L11 13L4 12Z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" strokeLinecap="round"/>
          </svg>
        </button>
      </form>
    </div>
  );
}

export default App;
