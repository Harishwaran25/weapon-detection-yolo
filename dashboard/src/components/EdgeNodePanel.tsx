import React from 'react';
import type { EdgeNodeTelemetry } from '../types';
import { Cpu, Zap, Thermometer, HardDrive, CheckCircle2, Activity } from 'lucide-react';

export const EdgeNodePanel: React.FC = () => {
  const nodeInfo: EdgeNodeTelemetry = {
    nodeId: 'RPi-EDGE-01',
    nodeName: 'Server Room Raspberry Pi 4 Edge Node',
    hardware: 'Raspberry Pi 4 Model B (Quad-core ARM Cortex-A72 @ 1.5GHz)',
    cpuTempC: 48.5,
    cpuUsagePct: 26.4,
    ramUsagePct: 34.2,
    inferenceEngine: 'TensorFlow Lite Runtime (C++ API)',
    quantization: 'INT8 Quantized (models/best_int8.tflite)',
    avgLatencyMs: 14.2,
    status: 'OPTIMAL',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Node Status Banner */}
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ background: 'rgba(16, 185, 129, 0.15)', padding: '12px', borderRadius: '12px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
            <Cpu size={28} color="var(--accent-green)" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>{nodeInfo.nodeName}</h2>
              <span className="badge badge-normal">
                <CheckCircle2 size={12} /> {nodeInfo.status}
              </span>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              {nodeInfo.hardware}
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '8px 14px', borderRadius: '8px', border: '1px solid var(--border-color)', textAlign: 'right' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Avg Inference Latency</span>
            <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
              {nodeInfo.avgLatencyMs} ms
            </div>
          </div>
          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '8px 14px', borderRadius: '8px', border: '1px solid var(--border-color)', textAlign: 'right' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Edge FPS Throughput</span>
            <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>
              {(1000 / nodeInfo.avgLatencyMs).toFixed(1)} FPS
            </div>
          </div>
        </div>
      </div>

      {/* Telemetry Metrics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
        {/* CPU Temp */}
        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              <Thermometer size={16} color="#f59e0b" /> Core Thermal Temp
            </div>
            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, color: '#f59e0b' }}>{nodeInfo.cpuTempC}°C</span>
          </div>
          <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ width: `${(nodeInfo.cpuTempC / 85) * 100}%`, height: '100%', background: 'linear-gradient(90deg, #10b981, #f59e0b)' }} />
          </div>
        </div>

        {/* CPU Usage */}
        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              <Activity size={16} color="var(--accent-cyan)" /> CPU Load Factor
            </div>
            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--accent-cyan)' }}>{nodeInfo.cpuUsagePct}%</span>
          </div>
          <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ width: `${nodeInfo.cpuUsagePct}%`, height: '100%', background: 'var(--accent-cyan)' }} />
          </div>
        </div>

        {/* RAM Usage */}
        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              <HardDrive size={16} color="var(--accent-purple)" /> Memory Allocation
            </div>
            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--accent-purple)' }}>{nodeInfo.ramUsagePct}%</span>
          </div>
          <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ width: `${nodeInfo.ramUsagePct}%`, height: '100%', background: 'var(--accent-purple)' }} />
          </div>
        </div>
      </div>

      {/* Comparison: Full PyTorch vs TFLite Edge Model */}
      <div className="glass-panel" style={{ padding: '20px' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Zap size={18} color="var(--accent-cyan)" /> Model Optimization Comparison Matrix
        </h3>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                <th style={{ padding: '10px' }}>MODEL FORMAT</th>
                <th style={{ padding: '10px' }}>FILE SIZE</th>
                <th style={{ padding: '10px' }}>TARGET HARDWARE</th>
                <th style={{ padding: '10px' }}>LATENCY (MS)</th>
                <th style={{ padding: '10px' }}>PRECISION DROP</th>
                <th style={{ padding: '10px' }}>STATUS</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '12px 10px', fontWeight: 700 }}>YOLOv5 PyTorch (.pt)</td>
                <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)' }}>14.8 MB</td>
                <td style={{ padding: '12px 10px' }}>NVIDIA GPU Server / Workstation</td>
                <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>6.5 ms</td>
                <td style={{ padding: '12px 10px' }}>Baseline (0%)</td>
                <td style={{ padding: '12px 10px' }}><span className="badge badge-cyan">Server Main</span></td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(16,185,129,0.05)' }}>
                <td style={{ padding: '12px 10px', fontWeight: 700, color: 'var(--accent-green)' }}>TFLite INT8 Quantized (.tflite)</td>
                <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)', color: 'var(--accent-green)' }}>3.9 MB (4x smaller)</td>
                <td style={{ padding: '12px 10px' }}>Raspberry Pi 4 / 5 Edge Node</td>
                <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)', color: 'var(--accent-green)' }}>14.2 ms</td>
                <td style={{ padding: '12px 10px', color: 'var(--accent-green)' }}>-0.8% mAP</td>
                <td style={{ padding: '12px 10px' }}><span className="badge badge-normal">Active Edge</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
