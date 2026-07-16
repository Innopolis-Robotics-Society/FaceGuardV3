import { useEffect, useState } from 'react';
import { Trash2, Edit2, Search, ArrowUp, ArrowDown, AlertCircle } from 'lucide-react';

interface Employee {
  id: number;
  name: string;
  registration_date: string;
  status: string;
  start_date: string | null;
  expiration_date: string | null;
  last_seen: string | null;
}

export default function Employees() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState('');
  const [sortCol, setSortCol] = useState<keyof Employee>('id');
  const [sortDesc, setSortDesc] = useState(false);

  const [editingEmp, setEditingEmp] = useState<Employee | null>(null);

  // Bulk selection state
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  // Edit Form State
  const [editName, setEditName] = useState('');
  const [editStatus, setEditStatus] = useState('Permanent');
  const [editStart, setEditStart] = useState('');
  const [editEnd, setEditEnd] = useState('');
  const [editError, setEditError] = useState('');

  const minDateTime = new Date();
  const pad = (n: number) => n.toString().padStart(2, '0');
  const minDateTimeStr = `${minDateTime.getFullYear()}-${pad(minDateTime.getMonth() + 1)}-${pad(minDateTime.getDate())}T${pad(minDateTime.getHours())}:${pad(minDateTime.getMinutes())}`;

  const fetchEmployees = () => {
    fetch('http://localhost:8000/api/employees', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
    })
      .then(res => res.json())
      .then(data => {
        setEmployees(data);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchEmployees();
  }, []);

  const handleDelete = (id: number) => {
    if (!confirm('Are you sure you want to delete this employee?')) return;
    fetch(`http://localhost:8000/api/employees/${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
    })
      .then(() => {
        setSelectedIds(prev => {
          const newSet = new Set(prev);
          newSet.delete(id);
          return newSet;
        });
        fetchEmployees();
      });
  };

  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) return;
    if (!confirm(`Are you sure you want to delete ${selectedIds.size} employees?`)) return;

    for (const id of Array.from(selectedIds)) {
      await fetch(`http://localhost:8000/api/employees/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
      });
    }

    setSelectedIds(new Set());
    fetchEmployees();
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === sorted.length && sorted.length > 0) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(sorted.map(e => e.id)));
    }
  };

  const toggleSelect = (id: number) => {
    const newSet = new Set(selectedIds);
    if (newSet.has(id)) newSet.delete(id);
    else newSet.add(id);
    setSelectedIds(newSet);
  };

  const handleEditClick = (emp: Employee) => {
    setEditError('');
    setEditingEmp(emp);
    setEditName(emp.name);
    setEditStatus(emp.status);

    // For editing, we should allow the previous dates to be shown,
    // but the validation should still enforce end > start and start >= now (if changed)
    // Helper to format Date to local YYYY-MM-DDThh:mm string
    const formatLocal = (dateStr: string) => {
      const d = new Date(dateStr);
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
    };

    setEditStart(emp.start_date ? formatLocal(emp.start_date) : '');
    setEditEnd(emp.expiration_date ? formatLocal(emp.expiration_date) : '');
  };

  const saveEdit = () => {
    if (!editingEmp) return;
    setEditError('');

    if (!editName) {
      setEditError('Please enter a name.');
      return;
    }

    let finalStart = null;
    let finalEnd = null;
    if (editStatus === 'Temporary') {
      if (!editStart || !editEnd) {
        setEditError('Please enter both start and expiration dates.');
        return;
      }

      const startDt = new Date(editStart);
      const endDt = new Date(editEnd);

      if (isNaN(startDt.getTime()) || isNaN(endDt.getTime())) {
        setEditError('Please enter valid dates.');
        return;
      }

      const now = new Date();
      now.setSeconds(0, 0);

      // Strict validation
      // If user edits the date to something past, reject. (unless they didn't change it, but simplest is to enforce it always)
      if (startDt < now) {
        // Only error if the start time is strictly earlier than now 
        // AND the user actually modified the start time (or it's a new temporary record).
        // Let's enforce that any temporary access saved from now on must be valid in the future.
        setEditError('Start time cannot be in the past.');
        return;
      }
      if (endDt <= startDt) {
        setEditError('Expiration time must be at least 1 minute after start time.');
        return;
      }

      const getLocalISO = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:00.000`;

      finalStart = getLocalISO(startDt);
      finalEnd = getLocalISO(endDt);
    }

    fetch(`http://localhost:8000/api/employees/${editingEmp.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
      },
      body: JSON.stringify({
        name: editName,
        status: editStatus,
        start_date: finalStart,
        expiration_date: finalEnd
      })
    }).then(async res => {
      if (res.ok) {
        setEditingEmp(null);
        fetchEmployees();
      } else {
        const d = await res.json();
        setEditError(d.detail || 'Failed to update employee.');
      }
    }).catch(() => {
      setEditError('Network error occurred.');
    });
  };

  const handleSort = (col: keyof Employee) => {
    if (sortCol === col) setSortDesc(!sortDesc);
    else {
      setSortCol(col);
      setSortDesc(false);
    }
  };

  const filtered = employees.filter(e => e.name.toLowerCase().includes(search.toLowerCase()));
  const sorted = [...filtered].sort((a, b) => {
    const valA = a[sortCol];
    const valB = b[sortCol];
    if (valA === valB) return 0;
    if (valA === null) return 1;
    if (valB === null) return -1;
    const cmp = valA > valB ? 1 : -1;
    return sortDesc ? -cmp : cmp;
  });

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Employees Directory</h2>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          {selectedIds.size > 0 && (
            <button className="btn btn-danger" onClick={handleBulkDelete}>
              <Trash2 size={16} /> Delete Selected ({selectedIds.size})
            </button>
          )}
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
      </div>

      <div className="glass-panel">
        <div className="table-container">
          {loading ? (
            <p>Loading...</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th style={{ width: 40 }}>
                    <input
                      type="checkbox"
                      checked={sorted.length > 0 && selectedIds.size === sorted.length}
                      onChange={toggleSelectAll}
                    />
                  </th>
                  <th onClick={() => handleSort('id')} style={{ cursor: 'pointer' }}>
                    ID {sortCol === 'id' && (sortDesc ? <ArrowDown size={14} /> : <ArrowUp size={14} />)}
                  </th>
                  <th onClick={() => handleSort('name')} style={{ cursor: 'pointer' }}>
                    Name {sortCol === 'name' && (sortDesc ? <ArrowDown size={14} /> : <ArrowUp size={14} />)}
                  </th>
                  <th onClick={() => handleSort('registration_date')} style={{ cursor: 'pointer' }}>
                    Registration {sortCol === 'registration_date' && (sortDesc ? <ArrowDown size={14} /> : <ArrowUp size={14} />)}
                  </th>
                  <th>Status</th>
                  <th>Access Window</th>
                  <th onClick={() => handleSort('last_seen')} style={{ cursor: 'pointer' }}>
                    Last Seen {sortCol === 'last_seen' && (sortDesc ? <ArrowDown size={14} /> : <ArrowUp size={14} />)}
                  </th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((emp) => (
                  <tr key={emp.id} style={{ background: selectedIds.has(emp.id) ? 'rgba(59, 130, 246, 0.1)' : '' }}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selectedIds.has(emp.id)}
                        onChange={() => toggleSelect(emp.id)}
                      />
                    </td>
                    <td>{emp.id}</td>
                    <td><strong>{emp.name}</strong></td>
                    <td>{new Date(emp.registration_date).toLocaleDateString()}</td>
                    <td>
                      <span className={emp.status === 'Permanent' ? 'badge success' : 'badge warning'}>
                        {emp.status}
                      </span>
                    </td>
                    <td>
                      {emp.status === 'Temporary' && emp.start_date && emp.expiration_date ? (
                        <span style={{ fontSize: '0.85em', color: 'var(--text-muted)' }}>
                          {new Date(emp.start_date).toLocaleString()} <br />
                          to {new Date(emp.expiration_date).toLocaleString()}
                        </span>
                      ) : '-'}
                    </td>
                    <td>
                      {emp.last_seen ? new Date(emp.last_seen).toLocaleString() : <span style={{ color: '#888' }}>Never</span>}
                    </td>
                    <td>
                      <button className="btn-icon" onClick={() => handleEditClick(emp)} title="Edit">
                        <Edit2 size={18} />
                      </button>
                      <button className="btn-icon" onClick={() => handleDelete(emp.id)} title="Delete">
                        <Trash2 size={18} />
                      </button>
                    </td>
                  </tr>
                ))}
                {sorted.length === 0 && (
                  <tr>
                    <td colSpan={8} style={{ textAlign: 'center' }}>No employees found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {editingEmp && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div className="glass-panel" style={{ width: 450, background: '#1e293b' }}>
            <h3>Edit Employee</h3>
            <div className="form-group" style={{ marginTop: '1rem' }}>
              <label>Name</label>
              <input className="form-control" value={editName} onChange={e => setEditName(e.target.value)} />
            </div>
            <div className="form-group">
              <label>Access Type</label>
              <select className="form-control" value={editStatus} onChange={e => setEditStatus(e.target.value)}>
                <option value="Permanent">Permanent</option>
                <option value="Temporary">Temporary</option>
              </select>
            </div>
            {editStatus === 'Temporary' && (
              <>
                <div className="form-group">
                  <label>Start Date & Time</label>
                  <input
                    type="datetime-local"
                    className="form-control"
                    min={minDateTimeStr}
                    value={editStart}
                    onChange={e => setEditStart(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>Expiration Date & Time</label>
                  <input
                    type="datetime-local"
                    className="form-control"
                    min={editStart || minDateTimeStr}
                    value={editEnd}
                    onChange={e => setEditEnd(e.target.value)}
                  />
                </div>
              </>
            )}

            {editError && (
              <div style={{
                background: 'rgba(239, 68, 68, 0.15)',
                borderLeft: '4px solid #ef4444',
                color: '#fca5a5',
                padding: '1rem',
                borderRadius: '6px',
                marginTop: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <AlertCircle size={20} style={{ flexShrink: 0 }} />
                <span>{editError}</span>
              </div>
            )}

            <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
              <button className="btn btn-primary" style={{ flex: 1 }} onClick={saveEdit}>Save</button>
              <button className="btn btn-danger" style={{ flex: 1, background: '#475569' }} onClick={() => setEditingEmp(null)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
