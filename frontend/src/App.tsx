import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { Camera, Users, UserPlus, Clock, LogOut } from 'lucide-react';
import { useState } from 'react';
import { useCamera } from './context/CameraContext';
import Recognition from './pages/Recognition';
import Registration from './pages/Registration';
import Employees from './pages/Employees';
import Logs from './pages/Logs';
import Auth from './pages/Auth';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return localStorage.getItem('auth_token') === 'authenticated';
  });
  
  const { isRecognizing } = useCamera();

  if (!isAuthenticated) {
    return <Auth onLogin={() => {
      localStorage.setItem('auth_token', 'authenticated');
      setIsAuthenticated(true);
    }} />;
  }

  return (
    <Router>
      <div className="app-container">
        <aside className="sidebar">
          <h1>FaceGuard</h1>
          <nav>
            <NavLink to="/employees" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <Users size={20} />
              <span>Employees</span>
            </NavLink>
            <NavLink to="/enroll" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <UserPlus size={20} />
              <span>Add Employee</span>
            </NavLink>
            <NavLink to="/logs" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <Clock size={20} />
              <span>Access Logs</span>
            </NavLink>
            <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <Camera size={20} />
                {isRecognizing && (
                  <div style={{
                    position: 'absolute', top: -2, right: -2, 
                    width: 8, height: 8, borderRadius: '50%', 
                    background: '#00ff00', boxShadow: '0 0 5px #00ff00'
                  }} title="Background recognition active" />
                )}
              </div>
              <span>Recognition</span>
            </NavLink>
          </nav>
          
          <button className="nav-link" style={{ marginTop: 'auto', background: 'transparent', border: 'none', color: 'var(--text-color)', cursor: 'pointer', textAlign: 'left' }} onClick={() => {
            localStorage.removeItem('auth_token');
            setIsAuthenticated(false);
          }}>
            <LogOut size={20} />
            <span>Logout</span>
          </button>
        </aside>
        
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Recognition />} />
            <Route path="/enroll" element={<Registration />} />
            <Route path="/employees" element={<Employees />} />
            <Route path="/logs" element={<Logs />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
