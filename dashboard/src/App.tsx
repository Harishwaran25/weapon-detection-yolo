import { useState } from 'react';
import type { CameraFeed, ThreatAlert, BoundingBox } from './types';
import { Navbar } from './components/Navbar';
import { CameraStreamCanvas } from './components/CameraStreamCanvas';
import { AlertPanel } from './components/AlertPanel';
import { AnalyticsPanel } from './components/AnalyticsPanel';
import { EdgeNodePanel } from './components/EdgeNodePanel';
import { DatasetPanel } from './components/DatasetPanel';
import { alarmAudio } from './utils/audio';

const INITIAL_CAMERAS: CameraFeed[] = [
  {
    id: 'CAM_01_ENTRANCE',
    name: 'Main Building Entrance',
    location: 'North Gate Lobby',
    status: 'ONLINE',
    resolution: '1920x1080',
    fps: 30,
    deviceType: 'RTSP IP Camera',
    latencyMs: 12,
    threatCount24h: 3,
  },
  {
    id: 'CAM_02_PARKING',
    name: 'Perimeter Parking Zone',
    location: 'East Wing Lot',
    status: 'ONLINE',
    resolution: '1920x1080',
    fps: 28,
    deviceType: 'RTSP IP Camera',
    latencyMs: 16,
    threatCount24h: 1,
  },
  {
    id: 'CAM_03_CASHIER',
    name: 'Cashier & Vault Counter',
    location: 'Main Finance Room',
    status: 'ONLINE',
    resolution: '1920x1080',
    fps: 30,
    deviceType: 'USB WebCam',
    latencyMs: 8,
    threatCount24h: 5,
  },
  {
    id: 'CAM_04_RPI_EDGE',
    name: 'Raspberry Pi Edge Node',
    location: 'Server Corridor',
    status: 'ONLINE',
    resolution: '1280x720',
    fps: 32,
    deviceType: 'Raspberry Pi Edge',
    latencyMs: 14.2,
    threatCount24h: 2,
  },
];

const INITIAL_ALERTS: ThreatAlert[] = [
  {
    id: 'ALT-109284',
    timestamp: '2026-08-30 20:15:22',
    epoch: Date.now() - 600000,
    cameraId: 'CAM_01_ENTRANCE',
    locationName: 'North Gate Lobby',
    threatClass: 'gun',
    confidence: 0.942,
    severity: 'CRITICAL',
    status: 'ACTIVE',
  },
  {
    id: 'ALT-109280',
    timestamp: '2026-08-30 19:42:10',
    epoch: Date.now() - 2500000,
    cameraId: 'CAM_03_CASHIER',
    locationName: 'Main Finance Room',
    threatClass: 'knife',
    confidence: 0.895,
    severity: 'HIGH',
    status: 'DISPATCHED',
  },
  {
    id: 'ALT-109275',
    timestamp: '2026-08-30 18:05:01',
    epoch: Date.now() - 8000000,
    cameraId: 'CAM_04_RPI_EDGE',
    locationName: 'Server Corridor',
    threatClass: 'heavy-weapon',
    confidence: 0.961,
    severity: 'CRITICAL',
    status: 'ACKNOWLEDGED',
  },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<'feeds' | 'alerts' | 'analytics' | 'edge' | 'dataset'>('feeds');
  const [cameras, setCameras] = useState<CameraFeed[]>(INITIAL_CAMERAS);
  const [alerts, setAlerts] = useState<ThreatAlert[]>(INITIAL_ALERTS);
  const [selectedCamId, setSelectedCamId] = useState<string>('CAM_01_ENTRANCE');
  const [soundEnabled, setSoundEnabled] = useState<boolean>(true);
  const [confThreshold, setConfThreshold] = useState<number>(0.45);
  const [activeThreat, setActiveThreat] = useState<BoundingBox | null>(null);

  const selectedCam = cameras.find((c) => c.id === selectedCamId) || cameras[0];
  const activeAlertCount = alerts.filter((a) => a.status === 'ACTIVE').length;

  const handleUpdateAlertStatus = (alertId: string, newStatus: ThreatAlert['status']) => {
    setAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, status: newStatus } : a))
    );
  };

  const handleInjectThreat = (threatType: 'gun' | 'knife' | 'heavy-weapon') => {
    const now = new Date();
    const timeStr = now.toISOString().replace('T', ' ').substring(0, 19);
    const confidence = threatType === 'gun' ? 0.94 : threatType === 'knife' ? 0.89 : 0.97;

    const newThreatBox: BoundingBox = {
      x: 240,
      y: 160,
      width: 70,
      height: 60,
      label: threatType,
      confidence: confidence,
      isThreat: true,
    };

    setActiveThreat(newThreatBox);

    const newAlert: ThreatAlert = {
      id: `ALT-${Math.floor(100000 + Math.random() * 900000)}`,
      timestamp: timeStr,
      epoch: Date.now(),
      cameraId: selectedCam.id,
      locationName: selectedCam.location,
      threatClass: threatType,
      confidence: confidence,
      severity: threatType === 'knife' ? 'HIGH' : 'CRITICAL',
      status: 'ACTIVE',
      boundingBoxes: [newThreatBox],
    };

    setAlerts((prev) => [newAlert, ...prev]);

    setCameras((prev) =>
      prev.map((c) => (c.id === selectedCam.id ? { ...c, status: 'ALERT' } : c))
    );

    if (soundEnabled) {
      alarmAudio.playSecuritySiren();
    }

    // Auto-clear active threat visual highlight after 12 seconds
    setTimeout(() => {
      setActiveThreat(null);
      setCameras((prev) =>
        prev.map((c) => (c.id === selectedCam.id ? { ...c, status: 'ONLINE' } : c))
      );
    }, 12000);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        activeAlertCount={activeAlertCount}
        soundEnabled={soundEnabled}
        setSoundEnabled={setSoundEnabled}
        onInjectThreat={handleInjectThreat}
      />

      <main style={{ flex: 1, padding: '24px', maxWidth: '1400px', width: '100%', margin: '0 auto' }}>
        {activeTab === 'feeds' && (
          <CameraStreamCanvas
            camera={selectedCam}
            activeThreat={activeThreat}
            confThreshold={confThreshold}
            setConfThreshold={setConfThreshold}
            onSelectCamera={setSelectedCamId}
            allCameras={cameras}
          />
        )}

        {activeTab === 'alerts' && (
          <AlertPanel alerts={alerts} onUpdateAlertStatus={handleUpdateAlertStatus} />
        )}

        {activeTab === 'analytics' && <AnalyticsPanel />}

        {activeTab === 'edge' && <EdgeNodePanel />}

        {activeTab === 'dataset' && <DatasetPanel />}
      </main>

      <footer style={{ borderTop: '1px solid var(--border-color)', padding: '16px 24px', textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
        Sentinel AI • Crime Detection using YOLOv5 & TensorFlow Lite • Real-time Edge Surveillance System
      </footer>
    </div>
  );
}
