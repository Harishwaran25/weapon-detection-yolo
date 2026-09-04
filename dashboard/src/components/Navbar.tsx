import React, { useState, useEffect } from 'react';
import { ShieldAlert, Cpu, Bell, Volume2, VolumeX, Radio, Crosshair, LayoutDashboard, BarChart3, HardDrive } from 'lucide-react';

interface NavbarProps {
  activeTab: 'surveillance' | 'inspector' | 'alerts' | 'analytics' | 'edge' | 'dataset';
  setActiveTab: (tab: 'surveillance' | 'inspector' | 'alerts' | 'analytics' | 'edge' | 'dataset') => void;
  activeAlertCount: number;
  soundEnabled: boolean;
  setSoundEnabled: (val: boolean | ((prev: boolean) => boolean)) => void;
  backendOnline: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  activeAlertCount,
  soundEnabled,
  setSoundEnabled,
  backendOnline,
}) => {
  const [timeStr, setTimeStr] = useState<string>('');

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString('en-US', { hour12: false }) + ' UTC+5:30');
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="glass-panel" style={{ borderRadius: 0, borderTop: 0, borderLeft: 0, borderRight: 0, padding: '12px 24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        {/* Brand logo & status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #ef4444, #991b1b)',
            padding: '10px',
            borderRadius: '12px',
            boxShadow: '0 0 20px rgba(239, 68, 68, 0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <ShieldAlert size={26} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1 style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.5px' }}>
                SENTINEL AI <span style={{ color: 'var(--accent-cyan)', fontWeight: 600, fontSize: '1rem' }}>SURVEILLANCE</span>
              </h1>
              <span className={`badge ${backendOnline ? 'badge-cyan' : 'badge-critical'}`}>
                <Radio size={10} className={backendOnline ? 'pulse-alert' : ''} />
                {backendOnline ? 'API CONNECTED' : 'OFFLINE'}
              </span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              YOLOv5 Crime & Weapon Detection Suite • RTX 3050 CUDA Acceleration
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(0,0,0,0.35)', padding: '4px', borderRadius: '10px', border: '1px solid var(--border-color)', flexWrap: 'wrap' }}>
          <button
            onClick={() => setActiveTab('surveillance')}
            className={`btn ${activeTab === 'surveillance' ? 'btn-primary' : 'btn-ghost'}`}
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            <LayoutDashboard size={14} /> Live Camera
          </button>
          <button
            onClick={() => setActiveTab('inspector')}
            className={`btn ${activeTab === 'inspector' ? 'btn-primary' : 'btn-ghost'}`}
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            <Crosshair size={14} /> Threat Inspector
          </button>
          <button
            onClick={() => setActiveTab('alerts')}
            className={`btn ${activeTab === 'alerts' ? 'btn-primary' : 'btn-ghost'}`}
            style={{ fontSize: '0.8rem', padding: '6px 12px', position: 'relative' }}
          >
            <Bell size={14} /> Incidents
            {activeAlertCount > 0 && (
              <span style={{
                background: '#ef4444',
                color: '#fff',
                borderRadius: '10px',
                padding: '1px 6px',
                fontSize: '0.7rem',
                fontWeight: 800,
                marginLeft: '5px'
              }}>
                {activeAlertCount}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`btn ${activeTab === 'analytics' ? 'btn-primary' : 'btn-ghost'}`}
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            <BarChart3 size={14} /> Benchmark & mAP
          </button>
          <button
            onClick={() => setActiveTab('edge')}
            className={`btn ${activeTab === 'edge' ? 'btn-primary' : 'btn-ghost'}`}
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            <Cpu size={14} /> Telemetry
          </button>
          <button
            onClick={() => setActiveTab('dataset')}
            className={`btn ${activeTab === 'dataset' ? 'btn-primary' : 'btn-ghost'}`}
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            <HardDrive size={14} /> Dataset & Models
          </button>
        </nav>

        {/* Sound Toggle & System Status Clock */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Sound Toggle */}
          <button
            onClick={() => setSoundEnabled((prev: boolean) => !prev)}
            className="btn btn-ghost"
            style={{ padding: '8px', borderRadius: '8px' }}
            title={soundEnabled ? 'Disable Alarm Sound' : 'Enable Alarm Sound'}
          >
            {soundEnabled ? <Volume2 size={18} color="var(--accent-cyan)" /> : <VolumeX size={18} color="var(--text-muted)" />}
          </button>

          {/* Clock */}
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'right' }}>
            <div style={{ color: 'var(--text-main)', fontWeight: 700 }}>{timeStr}</div>
            <div style={{ fontSize: '0.7rem', color: backendOnline ? 'var(--accent-green)' : '#ef4444', display: 'flex', alignItems: 'center', gap: '4px', justifyContent: 'flex-end' }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: backendOnline ? '#10b981' : '#ef4444', display: 'inline-block' }}></span>
              {backendOnline ? 'SYSTEM OPERATIONAL' : 'BACKEND OFFLINE'}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
