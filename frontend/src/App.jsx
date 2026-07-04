import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import AnalyzePage from './pages/AnalyzePage';
import DashboardPage from './pages/DashboardPage';
import InterviewPage from './pages/InterviewPage';

// A simple PrivateRoute component to protect routes that require authentication
function PrivateRoute({ children }) {
  const token = localStorage.getItem('token');
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
}

// Interceptor listener to handle global unauthorized events
function GlobalAuthListener() {
  const navigate = useNavigate();

  useEffect(() => {
    const handleUnauthorized = () => {
      navigate('/login');
    };

    window.addEventListener('unauthorized', handleUnauthorized);
    return () => {
      window.removeEventListener('unauthorized', handleUnauthorized);
    };
  }, [navigate]);

  return null;
}

function App() {
  return (
    <BrowserRouter>
      <GlobalAuthListener />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        
        <Route 
          path="/analyze" 
          element={
            <PrivateRoute>
              <AnalyzePage />
            </PrivateRoute>
          } 
        />
        
        <Route 
          path="/dashboard" 
          element={
            <PrivateRoute>
              <DashboardPage />
            </PrivateRoute>
          } 
        />

        <Route 
          path="/interview" 
          element={
            <PrivateRoute>
              <InterviewPage />
            </PrivateRoute>
          } 
        />
        
        {/* Redirect root to login (or analyze if already authenticated via PrivateRoute logic if we want, but explicit redirect is safer) */}
        <Route path="/" element={<Navigate to="/analyze" replace />} />
        
        {/* Catch-all redirect */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;