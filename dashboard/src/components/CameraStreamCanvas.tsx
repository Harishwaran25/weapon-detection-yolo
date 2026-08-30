import React, { useRef, useEffect, useState } from 'react';
import type { CameraFeed, BoundingBox } from '../types';
import { Camera, AlertTriangle, ShieldCheck, Cpu, Sliders } from 'lucide-react';

interface CameraStreamCanvasProps {
  camera: CameraFeed;
  activeThreat: BoundingBox | null;
  confThreshold: number;
  setConfThreshold: (val: number) => void;
  onSelectCamera: (camId: string) => void;
  allCameras: CameraFeed[];
}

export const CameraStreamCanvas: React.FC<CameraStreamCanvasProps> = ({
  camera,
  activeThreat,
  confThreshold,
  setConfThreshold,
  onSelectCamera,
  allCameras,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [showOverlay, setShowOverlay] = useState(true);

  // Animated state for simulated persons & objects moving in frame
  const animState = useRef({
    tick: 0,
    person1: { x: 120, y: 150, vx: 1.2, vy: 0.3 },
    person2: { x: 420, y: 220, vx: -0.8, vy: 0.4 },
    threatObj: { x: 260, y: 180, vx: 0.5, vy: -0.2 },
  });

  useEffect(() => {
    let animId: number;

    const render = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const w = canvas.width;
      const h = canvas.height;
      const state = animState.current;
      state.tick += 1;

      // Move simulated targets
      state.person1.x += state.person1.vx;
      if (state.person1.x > w - 100 || state.person1.x < 50) state.person1.vx *= -1;

      state.person2.x += state.person2.vx;
      if (state.person2.x > w - 120 || state.person2.x < 100) state.person2.vx *= -1;

      // 1. Draw CCTV Background Gradient & Grid
      const bgGradient = ctx.createLinearGradient(0, 0, w, h);
      bgGradient.addColorStop(0, '#0a0d18');
      bgGradient.addColorStop(0.5, '#121829');
      bgGradient.addColorStop(1, '#080a12');
      ctx.fillStyle = bgGradient;
      ctx.fillRect(0, 0, w, h);

      // Security Camera Grid Lines
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
      ctx.lineWidth = 1;
      const gridSize = 40;
      for (let x = 0; x < w; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }
      for (let y = 0; y < h; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }

      // Draw simulated environment objects (doors, counter, corridor)
      ctx.fillStyle = 'rgba(255, 255, 255, 0.02)';
      ctx.fillRect(40, 40, 120, 200); // Doorway frame
      ctx.fillRect(w - 180, 80, 140, 160); // Counter desk

      // 2. Draw Simulated Pedestrian / Person shapes
      // Person 1 (Normal civilian)
      ctx.fillStyle = 'rgba(0, 229, 255, 0.2)';
      ctx.beginPath();
      ctx.arc(state.person1.x, state.person1.y - 40, 14, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillRect(state.person1.x - 12, state.person1.y - 24, 24, 60);

      // Person 2 (Unusual activity / subject)
      ctx.fillStyle = activeThreat ? 'rgba(239, 68, 68, 0.25)' : 'rgba(16, 185, 129, 0.2)';
      ctx.beginPath();
      ctx.arc(state.person2.x, state.person2.y - 40, 14, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillRect(state.person2.x - 12, state.person2.y - 24, 24, 60);

      // 3. Draw AI Detection Bounding Boxes if Overlay Enabled
      if (showOverlay) {
        // Normal Person Box
        const p1Box = {
          x: state.person1.x - 22,
          y: state.person1.y - 60,
          w: 44,
          h: 100,
          label: 'person',
          conf: 0.94,
          isThreat: false,
        };

        ctx.strokeStyle = '#10b981';
        ctx.lineWidth = 2;
        ctx.strokeRect(p1Box.x, p1Box.y, p1Box.w, p1Box.h);
        ctx.fillStyle = 'rgba(16, 185, 129, 0.85)';
        ctx.fillRect(p1Box.x, p1Box.y - 20, 90, 20);
        ctx.fillStyle = '#050b14';
        ctx.font = 'bold 11px JetBrains Mono';
        ctx.fillText(`${p1Box.label.toUpperCase()} ${p1Box.conf.toFixed(2)}`, p1Box.x + 4, p1Box.y - 6);

        // Simulated Weapon / Threat Box if Active
        if (activeThreat && activeThreat.confidence >= confThreshold) {
          const threatX = state.person2.x - 30;
          const threatY = state.person2.y - 30;
          const threatW = 65;
          const threatH = 55;

          // Glowing Threat Box
          ctx.shadowColor = '#ef4444';
          ctx.shadowBlur = 15;
          ctx.strokeStyle = '#ef4444';
          ctx.lineWidth = 3;
          ctx.strokeRect(threatX, threatY, threatW, threatH);
          ctx.shadowBlur = 0; // reset

          // Fill header badge
          ctx.fillStyle = '#ef4444';
          ctx.fillRect(threatX, threatY - 22, 140, 22);
          ctx.fillStyle = '#ffffff';
          ctx.font = 'bold 12px JetBrains Mono';
          ctx.fillText(`🚨 ${activeThreat.label.toUpperCase()} ${activeThreat.confidence.toFixed(2)}`, threatX + 4, threatY - 6);

          // Draw target reticle crosshair
          const cx = threatX + threatW / 2;
          const cy = threatY + threatH / 2;
          ctx.strokeStyle = 'rgba(239, 68, 68, 0.6)';
          ctx.beginPath();
          ctx.arc(cx, cy, 25, 0, Math.PI * 2);
          ctx.moveTo(cx - 35, cy);
          ctx.lineTo(cx + 35, cy);
          ctx.moveTo(cx, cy - 35);
          ctx.lineTo(cx, cy + 35);
          ctx.stroke();
        }
      }

      // 4. CCTV OSD HUD (Timestamp, Camera Name, FPS)
      const now = new Date();
      const timeString = now.toISOString().replace('T', ' ').substring(0, 19);

      // Top Left Camera Info
      ctx.fillStyle = 'rgba(5, 11, 20, 0.7)';
      ctx.fillRect(10, 10, 240, 36);
      ctx.strokeStyle = 'rgba(255,255,255,0.1)';
      ctx.strokeRect(10, 10, 240, 36);

      ctx.fillStyle = '#00e5ff';
      ctx.font = 'bold 12px JetBrains Mono';
      ctx.fillText(`REC ● [${camera.id}] ${camera.name}`, 18, 28);
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px JetBrains Mono';
      ctx.fillText(`${camera.deviceType} • ${camera.resolution}`, 18, 40);

      // Top Right Time & FPS
      ctx.fillStyle = 'rgba(5, 11, 20, 0.7)';
      ctx.fillRect(w - 220, 10, 210, 36);
      ctx.strokeRect(w - 220, 10, 210, 36);

      ctx.fillStyle = '#f1f5f9';
      ctx.font = '11px JetBrains Mono';
      ctx.fillText(timeString, w - 210, 28);
      ctx.fillStyle = '#10b981';
      ctx.fillText(`FPS: ${camera.fps} | Latency: ${camera.latencyMs}ms`, w - 210, 40);

      // Bottom Alert Banner if Threat Active
      if (activeThreat && activeThreat.confidence >= confThreshold) {
        ctx.fillStyle = 'rgba(239, 68, 68, 0.85)';
        ctx.fillRect(0, h - 35, w, 35);
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 13px Plus Jakarta Sans';
        ctx.fillText(`🚨 CRITICAL SECURITY ALERT: DETECTED ${activeThreat.label.toUpperCase()} (${(activeThreat.confidence * 100).toFixed(1)}% CONFIDENCE) ON ${camera.name}`, 20, h - 12);
      }

      animId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animId);
  }, [camera, activeThreat, confThreshold, showOverlay]);

  return (
    <div className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Video Header Controls */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Camera size={20} color="var(--accent-cyan)" />
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>
              {camera.name} <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>({camera.location})</span>
            </h2>
          </div>
          {activeThreat ? (
            <span className="badge badge-critical pulse-alert">
              <AlertTriangle size={12} /> THREAT ACTIVE
            </span>
          ) : (
            <span className="badge badge-normal">
              <ShieldCheck size={12} /> SECURE
            </span>
          )}
        </div>

        {/* Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* AI Bounding Box Overlay Toggle */}
          <button
            onClick={() => setShowOverlay(!showOverlay)}
            className={`btn ${showOverlay ? 'btn-primary' : 'btn-ghost'}`}
            style={{ fontSize: '0.75rem', padding: '6px 10px' }}
          >
            <Cpu size={14} /> AI Bounding Boxes: {showOverlay ? 'ON' : 'OFF'}
          </button>

          {/* Confidence Threshold Slider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(0,0,0,0.3)', padding: '4px 10px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <Sliders size={14} color="var(--accent-cyan)" />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Conf:</span>
            <input
              type="range"
              min="0.1"
              max="0.9"
              step="0.05"
              value={confThreshold}
              onChange={(e) => setConfThreshold(parseFloat(e.target.value))}
              style={{ width: '80px', accentColor: 'var(--accent-cyan)' }}
            />
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-cyan)' }}>
              {(confThreshold * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>

      {/* Canvas Viewport */}
      <div style={{ position: 'relative', width: '100%', borderRadius: '8px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.1)' }}>
        <div className="scanline-effect"></div>
        <canvas
          ref={canvasRef}
          width={800}
          height={450}
          style={{ width: '100%', height: 'auto', display: 'block', aspectRatio: '16/9' }}
        />
      </div>

      {/* Camera Grid Switcher bar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
        {allCameras.map((cam) => (
          <button
            key={cam.id}
            onClick={() => onSelectCamera(cam.id)}
            style={{
              background: cam.id === camera.id ? 'rgba(0, 229, 255, 0.12)' : 'rgba(255,255,255,0.03)',
              border: `1px solid ${cam.id === camera.id ? 'var(--accent-cyan)' : 'var(--border-color)'}`,
              borderRadius: '8px',
              padding: '10px',
              textAlign: 'left',
              cursor: 'pointer',
              color: 'var(--text-main)',
              transition: 'all 0.2s ease',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{cam.id}</span>
              <span className={`badge ${cam.status === 'ALERT' ? 'badge-critical' : 'badge-normal'}`} style={{ fontSize: '0.65rem', padding: '2px 6px' }}>
                {cam.status}
              </span>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
              {cam.name}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '4px' }}>
              {cam.fps} FPS • {cam.latencyMs}ms
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
