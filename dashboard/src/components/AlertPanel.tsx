import React, { useState } from 'react';
import type { ThreatAlert } from '../types';
import { ShieldAlert, AlertTriangle, CheckCircle, XCircle, Download, Filter, Send, Eye, Trash2, RefreshCw } from 'lucide-react';

interface AlertPanelProps {
  alerts: ThreatAlert[];
  onRefreshAlerts?: () => void;
  onUpdateAlertStatus: (alertId: string, newStatus: ThreatAlert['status']) => void;
}

export const AlertPanel: React.FC<AlertPanelProps> = ({ alerts, onRefreshAlerts, onUpdateAlertStatus }) => {
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [selectedAlert, setSelectedAlert] = useState<ThreatAlert | null>(null);

  const filteredAlerts = alerts.filter((a) => {
    if (filterSeverity !== 'ALL' && a.severity !== filterSeverity) return false;
    if (filterStatus !== 'ALL' && a.status !== filterStatus) return false;
    return true;
  });

  const exportJSON = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(alerts, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `crime_surveillance_alerts_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const exportCSV = () => {
    const headers = ['Event ID', 'Timestamp', 'Camera', 'Threat Class', 'Confidence', 'Severity', 'Status'];
    const rows = alerts.map((a) => [
      a.id,
      a.timestamp,
      a.cameraId,
      a.threatClass,
      (a.confidence * 100).toFixed(1) + '%',
      a.severity,
      a.status,
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers, ...rows].map((e) => e.join(',')).join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `crime_surveillance_audit_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  const handleDeleteAlert = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await fetch(`/api/alerts/${id}`, { method: 'DELETE' });
      if (onRefreshAlerts) onRefreshAlerts();
    } catch (err) {
      console.error('Delete alert error:', err);
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm('Clear all logged incident alerts?')) return;
    try {
      await fetch('/api/alerts', { method: 'DELETE' });
      if (onRefreshAlerts) onRefreshAlerts();
    } catch (err) {
      console.error('Clear alerts error:', err);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Header & Controls */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ background: 'rgba(239, 68, 68, 0.15)', padding: '10px', borderRadius: '10px' }}>
            <ShieldAlert size={24} color="#ef4444" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>Incident Command & Audit Log</h2>
              <span className="badge badge-critical">{alerts.length} LOGGED</span>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Real-time threat alerts and surveillance audit events from YOLOv5 AI detector
            </p>
          </div>
        </div>

        {/* Filter Controls & Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {/* Severity Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(0,0,0,0.3)', padding: '6px 12px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <Filter size={14} color="var(--accent-cyan)" />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Severity:</span>
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              style={{ background: 'transparent', color: 'var(--text-main)', border: 'none', fontSize: '0.8rem', fontWeight: 600, outline: 'none', cursor: 'pointer' }}
            >
              <option value="ALL" style={{ background: '#0f1423' }}>ALL</option>
              <option value="CRITICAL" style={{ background: '#0f1423' }}>CRITICAL</option>
              <option value="HIGH" style={{ background: '#0f1423' }}>HIGH</option>
            </select>
          </div>

          {/* Status Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(0,0,0,0.3)', padding: '6px 12px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Status:</span>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              style={{ background: 'transparent', color: 'var(--text-main)', border: 'none', fontSize: '0.8rem', fontWeight: 600, outline: 'none', cursor: 'pointer' }}
            >
              <option value="ALL" style={{ background: '#0f1423' }}>ALL STATUSES</option>
              <option value="ACTIVE" style={{ background: '#0f1423' }}>ACTIVE</option>
              <option value="DISPATCHED" style={{ background: '#0f1423' }}>DISPATCHED</option>
              <option value="ACKNOWLEDGED" style={{ background: '#0f1423' }}>ACKNOWLEDGED</option>
              <option value="FALSE_ALARM" style={{ background: '#0f1423' }}>FALSE ALARM</option>
            </select>
          </div>

          {onRefreshAlerts && (
            <button onClick={onRefreshAlerts} className="btn btn-ghost" title="Refresh alerts">
              <RefreshCw size={14} />
            </button>
          )}

          <button onClick={exportCSV} className="btn btn-ghost" style={{ fontSize: '0.8rem', padding: '6px 12px' }}>
            <Download size={14} /> CSV
          </button>
          <button onClick={exportJSON} className="btn btn-ghost" style={{ fontSize: '0.8rem', padding: '6px 12px' }}>
            <Download size={14} /> JSON
          </button>
          {alerts.length > 0 && (
            <button onClick={handleClearAll} className="btn btn-ghost" style={{ fontSize: '0.8rem', padding: '6px 10px', color: '#fca5a5' }} title="Clear All">
              <Trash2 size={14} /> Clear
            </button>
          )}
        </div>
      </div>

      {/* Incidents Table */}
      <div style={{ overflowX: 'auto', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ background: 'rgba(0,0,0,0.4)', borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
              <th style={{ padding: '12px 16px' }}>EVENT ID</th>
              <th style={{ padding: '12px 16px' }}>TIMESTAMP</th>
              <th style={{ padding: '12px 16px' }}>CAMERA / SOURCE</th>
              <th style={{ padding: '12px 16px' }}>THREAT CLASS</th>
              <th style={{ padding: '12px 16px' }}>CONFIDENCE</th>
              <th style={{ padding: '12px 16px' }}>SEVERITY</th>
              <th style={{ padding: '12px 16px' }}>STATUS</th>
              <th style={{ padding: '12px 16px', textAlign: 'right' }}>ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            {filteredAlerts.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No security incidents recorded. System running clear.
                </td>
              </tr>
            ) : (
              filteredAlerts.map((alert) => (
                <tr
                  key={alert.id || alert.event_id}
                  onClick={() => setSelectedAlert(alert)}
                  style={{
                    borderBottom: '1px solid rgba(255,255,255,0.05)',
                    background: alert.status === 'ACTIVE' ? 'rgba(239, 68, 68, 0.06)' : 'transparent',
                    cursor: 'pointer',
                    transition: 'background 0.2s ease',
                  }}
                >
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                    {alert.id || alert.event_id}
                  </td>
                  <td style={{ padding: '12px 16px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {alert.timestamp}
                  </td>
                  <td style={{ padding: '12px 16px', fontWeight: 600 }}>
                    {alert.cameraId}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{
                      fontWeight: 800,
                      color: alert.threatClass.includes('gun') || alert.threatClass.includes('heavy') ? '#ef4444' : '#f59e0b',
                      textTransform: 'uppercase',
                      fontFamily: 'var(--font-mono)',
                    }}>
                      🚨 {alert.threatClass}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                    {(alert.confidence * 100).toFixed(1)}%
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span className={`badge ${alert.severity === 'CRITICAL' ? 'badge-critical' : 'badge-high'}`}>
                      {alert.severity}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      padding: '3px 8px',
                      borderRadius: '4px',
                      background:
                        alert.status === 'DISPATCHED' ? 'rgba(16,185,129,0.2)' :
                        alert.status === 'ACKNOWLEDGED' ? 'rgba(59,130,246,0.2)' :
                        alert.status === 'FALSE_ALARM' ? 'rgba(100,116,139,0.2)' : 'rgba(239,68,68,0.2)',
                      color:
                        alert.status === 'DISPATCHED' ? '#34d399' :
                        alert.status === 'ACKNOWLEDGED' ? '#60a5fa' :
                        alert.status === 'FALSE_ALARM' ? '#94a3b8' : '#fca5a5',
                    }}>
                      {alert.status}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '6px' }}>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedAlert(alert);
                        }}
                        className="btn btn-ghost"
                        style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                      >
                        <Eye size={14} /> View
                      </button>
                      {alert.status === 'ACTIVE' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onUpdateAlertStatus(alert.id || alert.event_id!, 'DISPATCHED');
                          }}
                          className="btn btn-danger"
                          style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                        >
                          <Send size={12} /> Dispatch
                        </button>
                      )}
                      <button
                        onClick={(e) => handleDeleteAlert(alert.id || alert.event_id!, e)}
                        className="btn btn-ghost"
                        style={{ padding: '4px 6px', color: '#fca5a5' }}
                        title="Delete record"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Snapshot Modal Preview */}
      {selectedAlert && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.85)',
          backdropFilter: 'blur(8px)',
          zIndex: 100,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px',
        }}>
          <div className="glass-panel" style={{ maxWidth: '680px', width: '100%', padding: '24px', position: 'relative' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <AlertTriangle size={24} color="#ef4444" />
                <div>
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 800 }}>Incident Snapshot Evidence</h3>
                  <span style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
                    {selectedAlert.id || selectedAlert.event_id}
                  </span>
                </div>
              </div>
              <button onClick={() => setSelectedAlert(null)} className="btn btn-ghost" style={{ padding: '6px 12px' }}>
                ✕ Close
              </button>
            </div>

            {/* Snapshot Display */}
            <div style={{
              position: 'relative',
              width: '100%',
              minHeight: '280px',
              maxHeight: '400px',
              background: '#070a14',
              borderRadius: '8px',
              border: '2px solid #ef4444',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '16px',
              overflow: 'hidden',
            }}>
              {selectedAlert.snapshotUrl ? (
                <img
                  src={selectedAlert.snapshotUrl}
                  alt="Snapshot evidence"
                  style={{ width: '100%', height: 'auto', maxHeight: '400px', objectFit: 'contain', display: 'block' }}
                />
              ) : (
                <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  <ShieldAlert size={40} color="#ef4444" style={{ marginBottom: '10px' }} />
                  <p>Real-time Threat Recorded ({selectedAlert.threatClass.toUpperCase()})</p>
                </div>
              )}
            </div>

            {/* Details */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '18px', fontSize: '0.85rem' }}>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Camera Source:</span> <strong>{selectedAlert.cameraId}</strong>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Detected Threat:</span> <strong style={{ color: '#ef4444', textTransform: 'uppercase' }}>{selectedAlert.threatClass}</strong>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Confidence:</span> <strong>{(selectedAlert.confidence * 100).toFixed(1)}%</strong>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Status:</span> <strong>{selectedAlert.status}</strong>
              </div>
            </div>

            {/* Operator Actions */}
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
              <button
                onClick={() => {
                  onUpdateAlertStatus(selectedAlert.id || selectedAlert.event_id!, 'FALSE_ALARM');
                  setSelectedAlert(null);
                }}
                className="btn btn-ghost"
              >
                <XCircle size={14} /> False Alarm
              </button>
              <button
                onClick={() => {
                  onUpdateAlertStatus(selectedAlert.id || selectedAlert.event_id!, 'ACKNOWLEDGED');
                  setSelectedAlert(null);
                }}
                className="btn btn-ghost"
                style={{ color: '#60a5fa' }}
              >
                <CheckCircle size={14} /> Acknowledge
              </button>
              <button
                onClick={() => {
                  onUpdateAlertStatus(selectedAlert.id || selectedAlert.event_id!, 'DISPATCHED');
                  setSelectedAlert(null);
                }}
                className="btn btn-danger"
              >
                <Send size={14} /> Dispatch Security Force
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
