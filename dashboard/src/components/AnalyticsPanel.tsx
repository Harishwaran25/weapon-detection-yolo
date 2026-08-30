import React from 'react';
import type { ModelMetric } from '../types';
import { BarChart3, TrendingUp, ShieldCheck, Target, Award, Layers } from 'lucide-react';

export const AnalyticsPanel: React.FC = () => {
  const metrics: ModelMetric[] = [
    { className: 'Gun / Firearm', precision: 0.942, recall: 0.915, map50: 0.938, map50_95: 0.684, sampleCount: 420 },
    { className: 'Knife / Edged Weapon', precision: 0.895, recall: 0.872, map50: 0.891, map50_95: 0.612, sampleCount: 310 },
    { className: 'Heavy Weapon / Rifle', precision: 0.961, recall: 0.938, map50: 0.954, map50_95: 0.721, sampleCount: 185 },
  ];

  const hourlyData = [
    { hour: '00:00', count: 2 },
    { hour: '03:00', count: 1 },
    { hour: '06:00', count: 4 },
    { hour: '09:00', count: 12 },
    { hour: '12:00', count: 18 },
    { hour: '15:00', count: 15 },
    { hour: '18:00', count: 24 },
    { hour: '21:00', count: 8 },
  ];

  const maxCount = Math.max(...hourlyData.map((d) => d.count));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <div className="glass-panel" style={{ padding: '16px', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ background: 'rgba(0, 229, 255, 0.15)', padding: '12px', borderRadius: '10px' }}>
            <Target size={24} color="var(--accent-cyan)" />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Overall mAP @ 0.5</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-main)', fontFamily: 'var(--font-mono)' }}>92.8%</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--accent-green)' }}>+2.4% vs baseline</div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '16px', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ background: 'rgba(16, 185, 129, 0.15)', padding: '12px', borderRadius: '10px' }}>
            <Award size={24} color="var(--accent-green)" />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Detection Accuracy</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>90.5%</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Controlled Test Benchmark</div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '16px', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ background: 'rgba(239, 68, 68, 0.15)', padding: '12px', borderRadius: '10px' }}>
            <ShieldCheck size={24} color="#ef4444" />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Precision / Recall</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fca5a5', fontFamily: 'var(--font-mono)' }}>93.3% / 90.8%</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>F1-Score: 0.920</div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '16px', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ background: 'rgba(139, 92, 246, 0.15)', padding: '12px', borderRadius: '10px' }}>
            <Layers size={24} color="var(--accent-purple)" />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Annotated Custom Images</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--accent-purple)', fontFamily: 'var(--font-mono)' }}>3,450+</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>3 Crime Object Classes</div>
          </div>
        </div>
      </div>

      {/* Main Charts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '20px' }}>
        {/* Hourly Threat Bar Chart */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <BarChart3 size={20} color="var(--accent-cyan)" />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>24-Hour Threat Frequency Intensity</h3>
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Detections by Hour</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'flex-end', gap: '12px', height: '220px', padding: '10px 0', borderBottom: '1px solid var(--border-color)' }}>
            {hourlyData.map((d) => {
              const heightPct = (d.count / maxCount) * 100;
              return (
                <div key={d.hour} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', justifyContent: 'flex-end', gap: '8px' }}>
                  <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>{d.count}</span>
                  <div
                    style={{
                      width: '100%',
                      maxWidth: '36px',
                      height: `${heightPct}%`,
                      background: 'linear-gradient(180deg, var(--accent-cyan), rgba(0, 229, 255, 0.1))',
                      borderRadius: '4px 4px 0 0',
                      transition: 'height 0.5s ease',
                      boxShadow: '0 0 10px rgba(0, 229, 255, 0.2)',
                    }}
                  />
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{d.hour}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Model Evaluation Metrics Breakdown */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <TrendingUp size={20} color="var(--accent-green)" />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Class-Wise YOLO Performance</h3>
            </div>
            <span className="badge badge-cyan">Held-out Test Set</span>
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', textAlign: 'left' }}>
                <th style={{ padding: '8px' }}>CLASS</th>
                <th style={{ padding: '8px' }}>PRECISION</th>
                <th style={{ padding: '8px' }}>RECALL</th>
                <th style={{ padding: '8px' }}>mAP@0.5</th>
                <th style={{ padding: '8px' }}>SAMPLES</th>
              </tr>
            </thead>
            <tbody>
              {metrics.map((m) => (
                <tr key={m.className} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '12px 8px', fontWeight: 700 }}>{m.className}</td>
                  <td style={{ padding: '12px 8px', fontFamily: 'var(--font-mono)', color: 'var(--accent-green)' }}>
                    {(m.precision * 100).toFixed(1)}%
                  </td>
                  <td style={{ padding: '12px 8px', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                    {(m.recall * 100).toFixed(1)}%
                  </td>
                  <td style={{ padding: '12px 8px', fontFamily: 'var(--font-mono)', fontWeight: 800, color: '#fca5a5' }}>
                    {(m.map50 * 100).toFixed(1)}%
                  </td>
                  <td style={{ padding: '12px 8px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                    {m.sampleCount}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
