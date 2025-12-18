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
      setStatus(`Error: ${error.message}`);
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