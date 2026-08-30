import React, { useState } from 'react';
import type { ThreatAlert } from '../types';
import { ShieldAlert, AlertTriangle, CheckCircle, XCircle, Download, Filter, Send, Eye } from 'lucide-react';

interface AlertPanelProps {
  alerts: ThreatAlert[];
  onUpdateAlertStatus: (alertId: string, newStatus: ThreatAlert['status']) => void;
}

export const AlertPanel: React.FC<AlertPanelProps> = ({ alerts, onUpdateAlertStatus }) => {
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [selectedAlert, setSelectedAlert] = useState<ThreatAlert | null>(null);

  const filteredAlerts = alerts.filter((a) => {
    if (filterSeverity !== 'ALL' && a.severity !== filterSeverity) return false;
    return true;
  });

  const exportJSON = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(alerts, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `crime_detection_alerts_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Header & Filters */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <ShieldAlert size={22} color="#ef4444" />
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Security Incident Command Log</h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Real-time threat alerts triggered by YOLOv5 / TFLite surveillance pipeline
            </p>
          </div>
        </div>

        {/* Action & Filter Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(0,0,0,0.3)', padding: '4px 10px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <Filter size={14} color="var(--accent-cyan)" />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Severity:</span>
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              style={{
                background: 'transparent',
                color: 'var(--text-main)',
                border: 'none',
                fontSize: '0.8rem',
                fontWeight: 600,
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              <option value="ALL" style={{ background: '#0f1423' }}>ALL SEVERITIES</option>
              <option value="CRITICAL" style={{ background: '#0f1423' }}>CRITICAL</option>
              <option value="HIGH" style={{ background: '#0f1423' }}>HIGH</option>
              <option value="MEDIUM" style={{ background: '#0f1423' }}>MEDIUM</option>
            </select>
          </div>

          <button onClick={exportJSON} className="btn btn-ghost" style={{ fontSize: '0.8rem', padding: '6px 12px' }}>
            <Download size={14} /> Export JSON Log
          </button>
        </div>
      </div>

      {/* Table of Incidents */}
      <div style={{ overflowX: 'auto', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ background: 'rgba(0,0,0,0.4)', borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
              <th style={{ padding: '12px 16px' }}>EVENT ID</th>
              <th style={{ padding: '12px 16px' }}>TIMESTAMP</th>
              <th style={{ padding: '12px 16px' }}>CAMERA</th>
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
                <td colSpan={8} style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No incident alerts logged for the selected filter.
                </td>
              </tr>
            ) : (
              filteredAlerts.map((alert) => (
                <tr
                  key={alert.id}
                  style={{
                    borderBottom: '1px solid rgba(255,255,255,0.05)',
                    background: alert.status === 'ACTIVE' ? 'rgba(239, 68, 68, 0.05)' : 'transparent',
                    transition: 'background 0.2s ease',
                  }}
                >
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                    {alert.id}
                  </td>
                  <td style={{ padding: '12px 16px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {alert.timestamp}
                  </td>
                  <td style={{ padding: '12px 16px', fontWeight: 600 }}>
                    {alert.cameraId}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{
                      fontWeight: 700,
                      color: alert.threatClass.includes('gun') || alert.threatClass.includes('weapon') ? '#ef4444' : '#f59e0b',
                      textTransform: 'uppercase',
                    }}>
                      🚨 {alert.threatClass}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                    {(alert.confidence * 100).toFixed(1)}%
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span className={`badge ${alert.severity === 'CRITICAL' ? 'badge-critical' : alert.severity === 'HIGH' ? 'badge-high' : 'badge-normal'}`}>
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
                        onClick={() => setSelectedAlert(alert)}
                        className="btn btn-ghost"
                        style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                        title="View Threat Snapshot"
                      >
                        <Eye size={14} /> View
                      </button>
                      {alert.status === 'ACTIVE' && (
                        <>
                          <button
                            onClick={() => onUpdateAlertStatus(alert.id, 'DISPATCHED')}
                            className="btn btn-danger"
                            style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                            title="Dispatch Security Guard"
                          >
                            <Send size={12} /> Dispatch
                          </button>
                          <button
                            onClick={() => onUpdateAlertStatus(alert.id, 'ACKNOWLEDGED')}
                            className="btn btn-ghost"
                            style={{ padding: '4px 8px', fontSize: '0.75rem', color: '#60a5fa' }}
                          >
                            Ack
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Snapshot Modal Viewer */}
      {selectedAlert && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.8)',
          backdropFilter: 'blur(8px)',
          zIndex: 100,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px'
        }}>
          <div className="glass-panel" style={{ maxWidth: '650px', width: '100%', padding: '24px', position: 'relative' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <AlertTriangle size={24} color="#ef4444" />
                <div>
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 800 }}>Threat Snapshot Details</h3>
                  <span style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>{selectedAlert.id}</span>
                </div>
              </div>
              <button
                onClick={() => setSelectedAlert(null)}
                className="btn btn-ghost"
                style={{ padding: '6px 12px' }}
              >
                ✕ Close
              </button>
            </div>

            {/* Simulated Snapshot Graphic */}
            <div style={{
              position: 'relative',
              width: '100%',
              height: '320px',
              background: '#090d1a',
              borderRadius: '8px',
              border: '2px solid #ef4444',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '16px',
              overflow: 'hidden'
            }}>
              {/* Snapshot watermark */}
              <div style={{ position: 'absolute', top: 12, left: 12, background: 'rgba(0,0,0,0.7)', padding: '4px 10px', borderRadius: '4px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: '#ef4444' }}>
                SNAPSHOT CAPTURE • {selectedAlert.timestamp}
              </div>

              {/* Bounding Box Visualizer */}
              <div style={{
                width: '180px',
                height: '140px',
                border: '3px solid #ef4444',
                boxShadow: '0 0 20px rgba(239,68,68,0.5)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                padding: '6px',
                background: 'rgba(239, 68, 68, 0.1)',
                position: 'relative'
              }}>
                <span style={{ background: '#ef4444', color: '#fff', fontSize: '0.7rem', fontWeight: 800, padding: '2px 6px', fontFamily: 'var(--font-mono)' }}>
                  🚨 {selectedAlert.threatClass.toUpperCase()} ({(selectedAlert.confidence * 100).toFixed(1)}%)
                </span>
                <span style={{ fontSize: '0.65rem', color: '#fca5a5', fontFamily: 'var(--font-mono)' }}>
                  CAM: {selectedAlert.cameraId}
                </span>
              </div>
            </div>

            {/* Incident Details Summary */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '20px', fontSize: '0.85rem' }}>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Location:</span> <strong>{selectedAlert.locationName}</strong>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Detected Target:</span> <strong style={{ color: '#ef4444', textTransform: 'uppercase' }}>{selectedAlert.threatClass}</strong>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Confidence Score:</span> <strong>{(selectedAlert.confidence * 100).toFixed(1)}%</strong>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '6px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Current Status:</span> <strong>{selectedAlert.status}</strong>
              </div>
            </div>

            {/* Action Bar inside Modal */}
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => {
                  onUpdateAlertStatus(selectedAlert.id, 'FALSE_ALARM');
                  setSelectedAlert(null);
                }}
                className="btn btn-ghost"
              >
                <XCircle size={14} /> Mark False Alarm
              </button>
              <button
                onClick={() => {
                  onUpdateAlertStatus(selectedAlert.id, 'ACKNOWLEDGED');
                  setSelectedAlert(null);
                }}
                className="btn btn-ghost"
                style={{ color: '#60a5fa' }}
              >
                <CheckCircle size={14} /> Acknowledge
              </button>
              <button
                onClick={() => {
                  onUpdateAlertStatus(selectedAlert.id, 'DISPATCHED');
                  setSelectedAlert(null);
                }}
                className="btn btn-danger"
              >
                <Send size={14} /> Dispatch Security Response
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
