import { useState, useEffect, useCallback } from 'react';
import type { ThreatAlert } from './types';
import { Navbar } from './components/Navbar';
import { LiveSurveillance } from './components/LiveSurveillance';
import { ThreatInspector } from './components/ThreatInspector';
import { AlertPanel } from './components/AlertPanel';
import { AnalyticsPanel } from './components/AnalyticsPanel';
import { EdgeNodePanel } from './components/EdgeNodePanel';
import { DatasetPanel } from './components/DatasetPanel';

export default function App() {
  const [activeTab, setActiveTab] = useState<'surveillance' | 'inspector' | 'alerts' | 'analytics' | 'edge' | 'dataset'>('surveillance');
  const [alerts, setAlerts] = useState<ThreatAlert[]>([]);
  const [soundEnabled, setSoundEnabled] = useState<boolean>(true);
  const [confThreshold, setConfThreshold] = useState<number>(0.35);
  const [backendOnline, setBackendOnline] = useState<boolean>(false);

  // Poll backend health status
  const checkBackendHealth = useCallback(() => {
    fetch('/api/status')
      .then((res) => {
        if (res.ok) {
          setBackendOnline(true);
        } else {
          setBackendOnline(false);
        }
      })
      .catch(() => setBackendOnline(false));
  }, []);

  // Fetch real alerts from server
  const fetchAlerts = useCallback(() => {
    fetch('/api/alerts')
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setAlerts(data);
        }
      })
      .catch((err) => console.warn('Could not fetch alerts:', err));
  }, []);

  useEffect(() => {
    checkBackendHealth();
    fetchAlerts();
    const interval = setInterval(() => {
      checkBackendHealth();
      fetchAlerts();
    }, 4000);
    return () => clearInterval(interval);
  }, [checkBackendHealth, fetchAlerts]);

  const handleUpdateAlertStatus = async (alertId: string, newStatus: ThreatAlert['status']) => {
    try {
      await fetch(`/api/alerts/${alertId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      fetchAlerts();
    } catch (err) {
      console.error('Update status error:', err);
    }
  };

  const handleNewAlert = (newAlert: ThreatAlert) => {
    setAlerts((prev) => [newAlert, ...prev]);
  };

  const activeAlertCount = alerts.filter((a) => a.status === 'ACTIVE').length;

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        activeAlertCount={activeAlertCount}
        soundEnabled={soundEnabled}
        setSoundEnabled={setSoundEnabled}
        backendOnline={backendOnline}
      />

      <main style={{ flex: 1, padding: '24px', maxWidth: '1440px', width: '100%', margin: '0 auto' }}>
        {activeTab === 'surveillance' && (
          <LiveSurveillance
            confThreshold={confThreshold}
            setConfThreshold={setConfThreshold}
            soundEnabled={soundEnabled}
            onNewAlert={handleNewAlert}
          />
        )}

        {activeTab === 'inspector' && (
          <ThreatInspector
            confThreshold={confThreshold}
            soundEnabled={soundEnabled}
            onThreatDetected={fetchAlerts}
          />
        )}

        {activeTab === 'alerts' && (
          <AlertPanel
            alerts={alerts}
            onRefreshAlerts={fetchAlerts}
            onUpdateAlertStatus={handleUpdateAlertStatus}
          />
        )}

        {activeTab === 'analytics' && <AnalyticsPanel />}

        {activeTab === 'edge' && <EdgeNodePanel />}

        {activeTab === 'dataset' && <DatasetPanel />}
      </main>

      <footer style={{
        borderTop: '1px solid var(--border-color)',
        padding: '16px 24px',
        textAlign: 'center',
        fontSize: '0.8rem',
        color: 'var(--text-muted)',
        background: 'rgba(5, 8, 16, 0.7)',
      }}>
        Sentinel AI • Crime & Weapon Detection Surveillance System • Powered by YOLOv5, PyTorch & TensorFlow Lite
      </footer>
    </div>
  );
}
