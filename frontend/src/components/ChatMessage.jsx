export default function ChatMessage({ role, content, audioBase64 }) {
  const roleLabels = {
    curious: '🎤 Curious Host',
    explainer: '🎓 Expert Host',
    user: '👤 You'
  };

  const playAudio = () => {
    if (audioBase64) {
      const audio = new Audio(`data:audio/mp3;base64,${audioBase64}`);
      audio.play();
    }
  };

  return (
    <div className={`message ${role}`}>
      <div className="message-header">
        <span className="role">{roleLabels[role] || role}</span>
        {audioBase64 && (
          <button onClick={playAudio} className="play-btn">🔊 Play</button>
        )}
      </div>
      <div className="message-content">{content}</div>
    </div>
  );
}