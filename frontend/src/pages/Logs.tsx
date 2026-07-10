import { useEffect, useState, useRef } from 'react';
import { Search, ArrowUp, ArrowDown } from 'lucide-react';
import { useCamera } from '../context/CameraContext';

interface Log {
  id: number;
  name: string;
  time: string;
  status: string;
}

export default function Logs() {
  const [logs, setLogs] = useState<Log[]>([]);
  const [loading, setLoading] = useState(true);
  const { recognitionData, isRecognizing } = useCamera();
  
  const [search, setSearch] = useState('');
  const [sortCol, setSortCol] = useState<keyof Log>('time');
  const [sortDesc, setSortDesc] = useState(true);

  // We use a ref to prevent adding duplicate logs within a cooldown period
  const lastLogRef = useRef<{ name: string, status: string, time: number } | null>(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/logs')
      .then(res => res.json())
      .then(data => {
        setLogs(data);
        setLoading(false);
      });
  }, []);

  // Real-time logs updates
  useEffect(() => {
    if (!isRecognizing) return;
    
    let dbStatus = '';
    let dbName = recognitionData.name || 'Unknown';
    
    if (recognitionData.status === 'Access Granted') dbStatus = 'ACCESS_GRANTED';
    else if (recognitionData.status === 'Access Denied') {
      dbStatus = 'ACCESS_DENIED';
      dbName = 'UNKNOWN';
    }
    else if (recognitionData.status === 'SPOOF DETECTED') {
      dbStatus = 'SPOOF_ATTEMPT';
      dbName = 'UNKNOWN';
    }
    
    if (dbStatus) {
      const now = Date.now();
      const cooldown = 60000; // 1 minute, matching backend DB restriction
      
      const isDuplicate = lastLogRef.current && 
                          lastLogRef.current.name === dbName && 
                          lastLogRef.current.status === dbStatus && 
                          (now - lastLogRef.current.time) < cooldown;
                          
      if (!isDuplicate) {
        lastLogRef.current = { name: dbName, status: dbStatus, time: now };
        
        // Use a fake ID for UI rendering. A negative number ensures it doesn't collide with DB IDs until refresh
        const newLog: Log = {
          id: -now, 
          name: dbName,
          status: dbStatus,
          time: new Date().toISOString()
        };
        
        setLogs(prev => {
          // Check if already in the list to be safe (in case of strict mode double execution)
          if (prev.length > 0 && prev[0].name === newLog.name && prev[0].status === newLog.status && (new Date(prev[0].time).getTime() > now - 2000)) {
            return prev;
          }
          return [newLog, ...prev];
        });
      }
    }
  }, [recognitionData, isRecognizing]);

  const getStatusBadge = (status: string) => {
    if (status === 'ACCESS_GRANTED') return 'badge success';
    if (status === 'ACCESS_DENIED' || status === 'SPOOF_ATTEMPT') return 'badge danger';
    return 'badge neutral';
  };

  const handleSort = (col: keyof Log) => {
    if (sortCol === col) setSortDesc(!sortDesc);
    else {
      setSortCol(col);
      setSortDesc(false);
    }
  };

  const filtered = logs.filter(log => log.name.toLowerCase().includes(search.toLowerCase()));
  const sorted = [...filtered].sort((a, b) => {
    const valA = a[sortCol];
    const valB = b[sortCol];
    if (valA === valB) return 0;
    const cmp = valA > valB ? 1 : -1;
    return sortDesc ? -cmp : cmp;
  });

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Access Logs</h2>
        <div style={{ position: 'relative', width: 300 }}>
          <Search size={18} style={{ position: 'absolute', left: 10, top: 10, color: '#888' }} />
          <input 
            className="form-control" 
            style={{ paddingLeft: 35 }} 
            placeholder="Search by name..." 
            value={search} 
            onChange={e => setSearch(e.target.value)} 
          />
        </div>
      </div>
      
      <div className="glass-panel">
        <div className="table-container">
          {loading ? (
            <p>Loading...</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th onClick={() => handleSort('time')} style={{ cursor: 'pointer' }}>
                    Time {sortCol === 'time' && (sortDesc ? <ArrowDown size={14}/> : <ArrowUp size={14}/>)}
                  </th>
                  <th onClick={() => handleSort('name')} style={{ cursor: 'pointer' }}>
                    Name {sortCol === 'name' && (sortDesc ? <ArrowDown size={14}/> : <ArrowUp size={14}/>)}
                  </th>
                  <th onClick={() => handleSort('status')} style={{ cursor: 'pointer' }}>
                    Status {sortCol === 'status' && (sortDesc ? <ArrowDown size={14}/> : <ArrowUp size={14}/>)}
                  </th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((log) => (
                  <tr key={log.id}>
                    <td>{new Date(log.time).toLocaleString()}</td>
                    <td>{log.name}</td>
                    <td>
                      <span className={getStatusBadge(log.status)}>
                        {log.status.replace('_', ' ')}
                      </span>
                    </td>
                  </tr>
                ))}
                {sorted.length === 0 && (
                  <tr>
                    <td colSpan={3} style={{ textAlign: 'center' }}>No logs found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
