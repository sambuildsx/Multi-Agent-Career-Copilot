import React, { useState, useRef } from 'react';
import { UploadCloud, File, X, AlertCircle } from 'lucide-react';

export default function ResumeUpload({ onFileSelected, selectedFile }) {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const validateFile = (file) => {
    const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!validTypes.includes(file.type)) {
      setError('Please upload a PDF or Word document.');
      return false;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError('File size exceeds 5MB limit.');
      return false;
    }
    setError(null);
    return true;
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) onFileSelected(file);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (validateFile(file)) onFileSelected(file);
    }
  };

  const clearFile = () => {
    onFileSelected(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <div className="w-full">
      <div
        className={`relative glass-panel p-8 border-2 border-dashed rounded-2xl transition-all duration-300 flex flex-col items-center justify-center text-center
          ${dragActive ? 'border-blue-500 bg-blue-500/10' : 'border-slate-700 hover:border-slate-600'}
          ${selectedFile ? 'border-indigo-500/50 bg-indigo-500/5' : ''}
        `}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          accept=".pdf,.doc,.docx"
          onChange={handleChange}
        />

        {!selectedFile ? (
          <>
            <div className="w-16 h-16 rounded-full bg-slate-800/80 flex items-center justify-center mb-4 shadow-inner">
              <UploadCloud className="w-8 h-8 text-blue-400" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Upload Resume</h3>
            <p className="text-slate-400 mb-6 max-w-sm">
              Drag and drop your PDF or Word document here, or click to browse. Max size 5MB.
            </p>
            <button onClick={() => inputRef.current.click()} className="btn-secondary">
              Browse Files
            </button>
          </>
        ) : (
          <div className="w-full flex items-center justify-between bg-slate-900/80 p-4 rounded-xl border border-slate-700/50">
            <div className="flex items-center space-x-3">
              <File className="w-8 h-8 text-indigo-400" />
              <div className="text-left">
                <p className="font-medium text-slate-200 truncate max-w-[200px] sm:max-w-xs">{selectedFile.name}</p>
                <p className="text-xs text-slate-400">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
            </div>
            <button
              onClick={clearFile}
              className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 flex items-center space-x-2 text-red-400 bg-red-400/10 p-3 rounded-lg border border-red-400/20">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}
    </div>
  );
}