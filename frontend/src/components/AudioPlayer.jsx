import { useState, useRef } from 'react';

export default function AudioPlayer({ audioBase64, label }) {
  const [playing, setPlaying] = useState(false);
  const audioRef = useRef(null);

  const togglePlay = () => {
    if (!audioRef.current) {
      audioRef.current = new Audio(`data:audio/mp3;base64,${audioBase64}`);
      audioRef.current.onended = () => setPlaying(false);
    }

    if (playing) {
      audioRef.current.pause();
      setPlaying(false);
    } else {
      audioRef.current.play();
      setPlaying(true);
    }
  };

  return (
    <button onClick={togglePlay} className="audio-player">
      {playing ? '⏸️' : '▶️'} {label}
    </button>
  );
}