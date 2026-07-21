import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/auth/LoginPage';
import SignupPage from './pages/auth/SignupPage';
import AnalyzePage from './pages/optimizer/AnalyzePage';
import DashboardPage from './pages/dashboard/DashboardPage';
import InterviewPage from './pages/interview/InterviewPage';
import ReportPage from './pages/optimizer/ReportPage';
import JobsPage from './pages/jobs/JobsPage';

// A simple PrivateRoute component to protect routes that require authentication
function PrivateRoute({ children }) {
  const token = localStorage.getItem('token');
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
}

// Redirect authenticated users trying to access landing, login, or signup back to the dashboard
function PublicRoute({ children }) {
  const token = localStorage.getItem('token');
  
  if (token) {
    return <Navigate to="/dashboard" replace />;
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
        {/* Isolated Landing and Auth routes */}
        <Route 
          path="/" 
          element={
            <PublicRoute>
              <LandingPage />
            </PublicRoute>
          } 
        />
        <Route 
          path="/login" 
          element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          } 
        />
        <Route 
          path="/signup" 
          element={
            <PublicRoute>
              <SignupPage />
            </PublicRoute>
          } 
        />
        
        {/* Authenticated Dashboard routes */}
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
        

        
        <Route 
          path="/report" 
          element={
            <PrivateRoute>
              <ReportPage />
            </PrivateRoute>
          } 
        />
        
        <Route 
          path="/jobs/:jobId" 
          element={
            <PrivateRoute>
              <JobsPage />
            </PrivateRoute>
          } 
        />
        
        {/* Catch-all redirect */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;