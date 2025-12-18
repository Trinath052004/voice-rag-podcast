import { useState } from 'react';
import UploadPDF from './components/UploadPDF';
import PodcastPlayer from './components/PodcastPlayer';
import ChatMessage from './components/ChatMessage';
import { askQuestion } from './api';
import './App.css';

function App() {
  const [pdfUploaded, setPdfUploaded] = useState(false);
  const [question, setQuestion] = useState('');
  const [chat, setChat] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setChat(prev => [...prev, { role: 'user', content: question }]);

    try {
      const result = await askQuestion(question);
      setChat(prev => [...prev, { role: 'explainer', content: result.explainer }]);
    } catch (error) {
      setChat(prev => [...prev, { role: 'error', content: error.message }]);
    } finally {
      setLoading(false);
      setQuestion('');
    }
  };

  return (
    <div className="app">
      <header>
        <h1>🎙️ Voice RAG Podcast</h1>
        <p>Upload a PDF and let AI hosts discuss it!</p>
      </header>

      <main>
        <section className="sidebar">
          <UploadPDF onUploadSuccess={() => setPdfUploaded(true)} />
          
          {pdfUploaded && (
            <div className="status-badge">✅ PDF Ready</div>
          )}
        </section>

        <section className="content">
          <PodcastPlayer />

          <div className="user-chat">
            <h3>💬 Ask a Question</h3>
            <div className="chat-messages">
              {chat.map((msg, i) => (
                <ChatMessage key={i} role={msg.role} content={msg.content} />
              ))}
            </div>
            
            <form onSubmit={handleAsk} className="chat-input">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask about the document..."
                disabled={loading}
              />
              <button type="submit" disabled={loading}>
                {loading ? '...' : 'Ask'}
              </button>
            </form>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;