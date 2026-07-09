import { useEffect, useState } from 'react';
import { Search, ArrowUp, ArrowDown } from 'lucide-react';

interface Log {
  id: number;
  name: string;
  time: string;
  status: string;
}

export default function Logs() {
  const [logs, setLogs] = useState<Log[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [search, setSearch] = useState('');
  const [sortCol, setSortCol] = useState<keyof Log>('time');
  const [sortDesc, setSortDesc] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/logs')
      .then(res => res.json())
      .then(data => {
        setLogs(data);
        setLoading(false);
      });
  }, []);

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
