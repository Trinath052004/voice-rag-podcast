import { useState } from 'react';
import { generatePodcastWithAudio } from '../api';
import ChatMessage from './ChatMessage';

export default function PodcastPlayer() {
  const [conversation, setConversation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [topic, setTopic] = useState('overview');

  const generateTurn = async () => {
    setLoading(true);
    try {
      const result = await generatePodcastWithAudio(topic);
      setConversation(result);
    } catch (error) {
      console.error('Error generating podcast:', error);
    } finally {
      setLoading(false);
    }
  };

  const playAll = () => {
    if (!conversation) return;
    
    const audios = [
      conversation.curious_audio,
      conversation.explainer_audio
    ].filter(Boolean);

    let index = 0;
    const playNext = () => {
      if (index < audios.length) {
        const audio = new Audio(`data:audio/mp3;base64,${audios[index]}`);
        audio.onended = () => {
          index++;
          playNext();
        };
        audio.play();
      }
    };
    playNext();
  };

  return (
    <div className="podcast-player">
      <h3>🎙️ AI Podcast</h3>
      
      <div className="controls">
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Topic (e.g., overview, main concepts)"
        />
        <button onClick={generateTurn} disabled={loading}>
          {loading ? 'Generating...' : '▶️ Generate Turn'}
        </button>
        {conversation && (
          <button onClick={playAll}>🔊 Play All</button>
        )}
      </div>

      {conversation && (
        <div className="conversation">
          <ChatMessage 
            role="curious" 
            content={conversation.curious}
            audioBase64={conversation.curious_audio}
          />
          <ChatMessage 
            role="explainer" 
            content={conversation.explainer}
            audioBase64={conversation.explainer_audio}
          />
        </div>
      )}
    </div>
  );
}