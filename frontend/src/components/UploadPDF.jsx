import { useState } from 'react';
import { uploadPDF } from '../api';

export default function UploadPDF({ onUploadSuccess }) {
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState('');

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setStatus('Uploading and processing...');

    try {
      const result = await uploadPDF(file);
      setStatus(`Success! Indexed ${result.chunks_indexed} chunks.`);
      onUploadSuccess?.(result);
    } catch (error) {
      console.error("Upload error:", error);
      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        setStatus(`Error: ${error.response.data.detail || error.message}`);
      } else if (error.request) {
        // The request was made but no response was received
        setStatus("Error: No response from server. Is the backend running?");
      } else {
        // Something happened in setting up the request that triggered an Error
        setStatus(`Error: ${error.message}`);
      }
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-section">
      <h3>📄 Upload PDF</h3>
      <input 
        type="file" 
        accept=".pdf" 
        onChange={handleUpload} 
        disabled={uploading}
      />
      {status && <p className="status">{status}</p>}
    </div>
  );
}