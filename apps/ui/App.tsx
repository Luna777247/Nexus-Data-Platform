
import React, { useEffect } from 'react';
import { HashRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useStore } from './store';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import DataExplorer from './pages/DataExplorer';
import Analytics from './pages/Analytics';
import LogSearch from './pages/LogSearch';
import QualityLineage from './pages/QualityLineage';
import Monitoring from './pages/Monitoring';
import UserManagement from './pages/UserManagement';
import Settings from './pages/Settings';
import Login from './pages/Login';

const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useStore();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

const App: React.FC = () => {
  const { theme } = useStore();

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  return (
    <HashRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        
        <Route path="/" element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }>
          <Route index element={<Dashboard />} />
          <Route path="explorer" element={<DataExplorer />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="logs" element={<LogSearch />} />
          <Route path="quality" element={<QualityLineage />} />
          <Route path="monitoring" element={<Monitoring />} />
          <Route path="users" element={<UserManagement />} />
          <Route path="settings" element={<Settings />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </HashRouter>
  );
};

export default App;
