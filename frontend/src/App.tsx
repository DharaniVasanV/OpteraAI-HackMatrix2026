import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import AuthLayout from './components/AuthLayout';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Inbox from './pages/Inbox';
import Opportunities from './pages/Opportunities';
import Meetings from './pages/Meetings';
import Calendar from './pages/Calendar';
import Knowledge from './pages/Knowledge';
import Career from './pages/Career';
import Learning from './pages/Learning';
import Resume from './pages/Resume';
import Applications from './pages/Applications';
import Notifications from './pages/Notifications';
import Analytics from './pages/Analytics';
import Agents from './pages/Agents';
import Settings from './pages/Settings';
import { AuthProvider } from './context/AuthContext';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Auth Routes */}
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
          </Route>

          {/* Protected Routes */}
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/inbox" replace />} />
            <Route path="inbox" element={<Inbox />} />
            <Route path="opportunities" element={<Opportunities />} />
            <Route path="meetings" element={<Meetings />} />
            <Route path="calendar" element={<Calendar />} />
            <Route path="knowledge" element={<Knowledge />} />
            <Route path="career" element={<Career />} />
            <Route path="learning" element={<Learning />} />
            <Route path="resume" element={<Resume />} />
            <Route path="applications" element={<Applications />} />
            <Route path="notifications" element={<Notifications />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="agents" element={<Agents />} />
            <Route path="settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/inbox" replace />} />
          </Route>
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
