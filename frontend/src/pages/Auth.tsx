import { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { isUsableJwt } from '../auth/token';
import { apiUrl } from '../lib/urls';

interface AuthProps {
  onLogin: (token: string) => void;
}

export default function Auth({ onLogin }: AuthProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    fetch(apiUrl('/api/login'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    }).then(async res => {
      if (res.ok) {
        const data = await res.json();
        if (typeof data.token === 'string' && isUsableJwt(data.token)) {
          onLogin(data.token);
        } else {
          setError('Invalid authentication response');
        }
      } else if (res.status === 429) {
        setError('Too many attempts. Please try again later.');
      } else {
        setError('Invalid login or password');
      }
    }).catch(() => {
      setError('An error occurred. Please try again.');
    });
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg-color)' }}>
      <div className="glass-panel" style={{ width: 400, textAlign: 'center' }}>
        <h2 style={{ marginBottom: '1.5rem', color: 'var(--primary-color)' }}>FaceGuard Login</h2>
        <form onSubmit={handleLogin}>
          <div className="form-group" style={{ textAlign: 'left' }}>
            <label>Username</label>
            <input className="form-control" value={username} onChange={e => setUsername(e.target.value)} autoFocus />
          </div>
          <div className="form-group" style={{ textAlign: 'left', position: 'relative' }}>
            <label>Password</label>
            <input 
              className="form-control" 
              type={showPassword ? "text" : "password"} 
              value={password} 
              onChange={e => setPassword(e.target.value)} 
              style={{ paddingRight: '40px' }}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              style={{
                position: 'absolute',
                right: '10px',
                bottom: '10px',
                background: 'none',
                border: 'none',
                color: 'var(--text-color)',
                cursor: 'pointer',
                opacity: 0.7,
              }}
            >
              {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
            </button>
          </div>
          {error && <p style={{ color: 'var(--danger-color)', marginBottom: '1rem' }}>{error}</p>}
          <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }}>
            Login
          </button>
        </form>
      </div>
    </div>
  );
}
