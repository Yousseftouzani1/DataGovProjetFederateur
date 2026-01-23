import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate
} from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import LoginPage from './pages/LoginPage';
import Shell from './components/layout/Shell';
import DashboardPage from './pages/DashboardPage';
import PIIDetectionPage from './pages/PIIDetectionPage';
import QualityPage from './pages/QualityPage';
import SignupPage from './pages/SignupPage';
import DataPipelinePage from './pages/DataPipelinePage';
import TaskQueuePage from './pages/TaskQueuePage';
import UsersPage from './pages/UsersPage';
import AuditLogsPage from './pages/AuditLogsPage';
import SettingsPage from './pages/SettingsPage';
import DiscoveryPage from './pages/DiscoveryPage';
import LandingPage from './pages/LandingPage';
import { RoleThemeProvider } from './context/RoleThemeContext';
import { ToastProvider } from './context/ToastContext';
import { RangerProvider } from './context/RangerContext';
import RoleGuard from './components/auth/RoleGuard';

import { useEffect } from 'react';
import { updateFavicon } from './utils/dynamicFavicon';

function App() {
  const user = useAuthStore((state) => state.user);

  useEffect(() => {
    updateFavicon(user?.role || 'default');
  }, [user?.role]);

  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={user ? <Navigate to="/dashboard" /> : <LandingPage />} />
        <Route path="/login" element={!user ? <LoginPage /> : <Navigate to="/dashboard" />} />
        <Route path="/signup" element={!user ? <SignupPage /> : <Navigate to="/dashboard" />} />

        {/* Protected Group */}
        <Route
          path="/*"
          element={
            user ? (
              <RoleThemeProvider>
                <RangerProvider>
                  <ToastProvider>
                    <Shell>
                      <Routes>
                        <Route path="/dashboard" element={<DashboardPage />} />
                        <Route
                          path="/pii"
                          element={
                            <RoleGuard allowedRoles={['admin', 'steward', 'annotator']}>
                              <PIIDetectionPage />
                            </RoleGuard>
                          }
                        />
                        <Route
                          path="/quality"
                          element={
                            <RoleGuard allowedRoles={['admin', 'steward']}>
                              <QualityPage />
                            </RoleGuard>
                          }
                        />
                        <Route
                          path="/datasets"
                          element={
                            <RoleGuard allowedRoles={['admin', 'steward', 'annotator']}>
                              <DataPipelinePage />
                            </RoleGuard>
                          }
                        />
                        <Route path="/tasks" element={<TaskQueuePage />} />
                        <Route
                          path="/users"
                          element={
                            <RoleGuard allowedRoles={['admin']}>
                              <UsersPage />
                            </RoleGuard>
                          }
                        />
                        <Route
                          path="/audit"
                          element={
                            <RoleGuard allowedRoles={['admin', 'steward']}>
                              <AuditLogsPage />
                            </RoleGuard>
                          }
                        />
                        <Route
                          path="/discovery"
                          element={
                            <RoleGuard allowedRoles={['admin', 'steward', 'annotator']}>
                              <DiscoveryPage />
                            </RoleGuard>
                          }
                        />
                        <Route
                          path="/settings"
                          element={
                            <RoleGuard allowedRoles={['admin']}>
                              <SettingsPage />
                            </RoleGuard>
                          }
                        />
                        {/* Fallback */}
                        <Route path="*" element={<Navigate to="/dashboard" />} />
                      </Routes>
                    </Shell>
                  </ToastProvider>
                </RangerProvider>
              </RoleThemeProvider>
            ) : (
              <Navigate to="/login" />
            )
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
