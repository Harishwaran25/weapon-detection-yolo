import React, { useRef, useEffect, useState, useCallback } from 'react';
import type { DetectionBox, ThreatAlert } from '../types';
import { Camera, AlertTriangle, ShieldCheck, Cpu, Sliders, Video, VideoOff } from 'lucide-react';
import { alarmAudio } from '../utils/audio';

interface LiveSurveillanceProps {
  confThreshold: number;
  setConfThreshold: (val: number) => void;
  soundEnabled: boolean;
  onNewAlert?: (alert: ThreatAlert) => void;
}

export const LiveSurveillance: React.FC<LiveSurveillanceProps> = ({
  confThreshold,
  setConfThreshold,
  soundEnabled,
  onNewAlert,
}) => {
  const [isWebcamActive, setIsWebcamActive] = useState(false);
  const [showOverlay, setShowOverlay] = useState(true);
  const [fps, setFps] = useState<number>(0);
  const [latencyMs, setLatencyMs] = useState<number>(0);
  const [detections, setDetections] = useState<DetectionBox[]>([]);
  const [activeThreat, setActiveThreat] = useState<string | null>(null);
  const [webcamError, setWebcamError] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const animFrameIdRef = useRef<number | null>(null);
  const isStreamingRef = useRef(false);
  const lastSendTimeRef = useRef(0);
  const activeThreatTimerRef = useRef<number | null>(null);

  // Initialize WebSocket connection
  const connectWebSocket = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/webcam`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('Surveillance WebSocket connected.');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.detections) {
            setDetections(data.detections);
            setLatencyMs(data.inference_ms || 0);
            setFps(data.fps || 0);

            if (data.threat_detected && data.top_threat) {
              setActiveThreat(data.top_threat);
              if (soundEnabled) {
                alarmAudio.playSecuritySiren();
              }
              if (onNewAlert && data.snapshot_url) {
                onNewAlert({
                  id: `ALT-${Date.now() % 100000}`,
                  timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
                  epoch: Date.now(),
                  cameraId: 'LIVE_WEBCAM',
                  locationName: 'Local Terminal Feed',
                  threatClass: data.top_threat,
                  confidence: data.detections[0]?.confidence || 0.85,
                  severity: data.top_threat === 'knife' ? 'HIGH' : 'CRITICAL',
                  status: 'ACTIVE',
                  snapshotUrl: data.snapshot_url,
                });
              }

              if (activeThreatTimerRef.current) clearTimeout(activeThreatTimerRef.current);
              activeThreatTimerRef.current = window.setTimeout(() => {
                setActiveThreat(null);
              }, 4000);
            }
          }
        } catch (e) {
          console.error('WS parse error:', e);
        }
      };

      ws.onclose = () => {
        console.log('Surveillance WebSocket closed. Will reconnect if active...');
      };

      wsRef.current = ws;
    } catch (e) {
      console.warn('WebSocket init failed:', e);
    }
  }, [soundEnabled, onNewAlert]);

  // Start Webcam
  const startWebcam = async () => {
    setWebcamError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' },
        audio: false,
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
        setIsWebcamActive(true);
        isStreamingRef.current = true;
        connectWebSocket();
      }
    } catch (err: any) {
      console.error('Webcam access error:', err);
      setWebcamError(err.message || 'Unable to access camera device. Check permissions.');
    }
  };

  // Stop Webcam
  const stopWebcam = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach((track) => track.stop());
      videoRef.current.srcObject = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (animFrameIdRef.current) {
      cancelAnimationFrame(animFrameIdRef.current);
      animFrameIdRef.current = null;
    }
    isStreamingRef.current = false;
    setIsWebcamActive(false);
    setDetections([]);
    setActiveThreat(null);
  };

  // Capture & stream frame loop
  useEffect(() => {
    let active = true;

    const streamLoop = () => {
      if (!active) return;

      const video = videoRef.current;
      const canvas = canvasRef.current;

      if (isWebcamActive && video && canvas && video.readyState >= 2) {
        const ctx = canvas.getContext('2d');
        if (ctx) {
          canvas.width = video.videoWidth || 640;
          canvas.height = video.videoHeight || 480;

          // Draw webcam video frame
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

          // Draw AI Detections Overlay
          if (showOverlay && detections.length > 0) {
            detections.forEach((det) => {
              if (det.confidence < confThreshold) return;

              const [x1, y1, x2, y2] = det.bbox;
              const w = x2 - x1;
              const h = y2 - y1;
              const isThreat = det.isThreat;

              // Box
              ctx.strokeStyle = isThreat ? '#ef4444' : '#10b981';
              ctx.lineWidth = isThreat ? 3 : 2;
              ctx.strokeRect(x1, y1, w, h);

              // Glow for threat
              if (isThreat) {
                ctx.shadowColor = '#ef4444';
                ctx.shadowBlur = 12;
                ctx.strokeRect(x1, y1, w, h);
                ctx.shadowBlur = 0;

                // Center target crosshair
                const cx = x1 + w / 2;
                const cy = y1 + h / 2;
                ctx.strokeStyle = 'rgba(239, 68, 68, 0.8)';
                ctx.beginPath();
                ctx.arc(cx, cy, 18, 0, Math.PI * 2);
                ctx.moveTo(cx - 24, cy);
                ctx.lineTo(cx + 24, cy);
                ctx.moveTo(cx, cy - 24);
                ctx.lineTo(cx, cy + 24);
                ctx.stroke();
              }

              // Tag badge
              const tag = `${det.label.toUpperCase()} ${(det.confidence * 100).toFixed(1)}%`;
              ctx.font = 'bold 12px JetBrains Mono';
              const textWidth = ctx.measureText(tag).width;

              ctx.fillStyle = isThreat ? '#ef4444' : '#10b981';
              ctx.fillRect(x1, Math.max(0, y1 - 22), textWidth + 12, 22);

              ctx.fillStyle = '#ffffff';
              ctx.fillText(tag, x1 + 6, Math.max(16, y1 - 6));
            });
          }

          // HUD OSD
          const now = new Date();
          const timeStr = now.toISOString().replace('T', ' ').substring(0, 19);

          ctx.fillStyle = 'rgba(9, 12, 21, 0.75)';
          ctx.fillRect(10, 10, 260, 36);
          ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
          ctx.strokeRect(10, 10, 260, 36);

          ctx.fillStyle = '#00e5ff';
          ctx.font = 'bold 11px JetBrains Mono';
          ctx.fillText(`● LIVE WEBCAM • ${canvas.width}x${canvas.height}`, 18, 26);
          ctx.fillStyle = '#94a3b8';
          ctx.font = '10px JetBrains Mono';
          ctx.fillText(`${timeStr}`, 18, 40);

          // Top right FPS & Latency
          ctx.fillStyle = 'rgba(9, 12, 21, 0.75)';
          ctx.fillRect(canvas.width - 180, 10, 170, 36);
          ctx.strokeRect(canvas.width - 180, 10, 170, 36);

          ctx.fillStyle = '#10b981';
          ctx.font = 'bold 11px JetBrains Mono';
          ctx.fillText(`FPS: ${fps.toFixed(1)}`, canvas.width - 170, 26);
          ctx.fillStyle = '#00e5ff';
          ctx.font = '10px JetBrains Mono';
          ctx.fillText(`GPU Latency: ${latencyMs.toFixed(1)}ms`, canvas.width - 170, 40);

          // Threat alert banner
          if (activeThreat) {
            ctx.fillStyle = 'rgba(239, 68, 68, 0.9)';
            ctx.fillRect(0, canvas.height - 36, canvas.width, 36);
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 14px Plus Jakarta Sans';
            ctx.fillText(`🚨 CRITICAL THREAT DETECTED: ${activeThreat.toUpperCase()} IN LIVE FEED`, 20, canvas.height - 12);
          }

          // Send frame via WebSocket (throttled to ~25 FPS = every 40ms)
          const nowMs = performance.now();
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && nowMs - lastSendTimeRef.current > 40) {
            lastSendTimeRef.current = nowMs;
            const b64 = canvas.toDataURL('image/jpeg', 0.65);
            wsRef.current.send(
              JSON.stringify({
                image: b64,
                conf: confThreshold,
                iou: 0.45,
                cameraId: 'LIVE_WEBCAM',
              })
            );
          }
        }
      }

      animFrameIdRef.current = requestAnimationFrame(streamLoop);
    };

    animFrameIdRef.current = requestAnimationFrame(streamLoop);

    return () => {
      active = false;
      if (animFrameIdRef.current) cancelAnimationFrame(animFrameIdRef.current);
    };
  }, [isWebcamActive, showOverlay, confThreshold, detections, activeThreat, fps, latencyMs]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      stopWebcam();
    };
  }, []);

  return (
    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Feed Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            background: isWebcamActive ? 'rgba(16, 185, 129, 0.2)' : 'rgba(0, 229, 255, 0.15)',
            padding: '10px',
            borderRadius: '10px',
            border: `1px solid ${isWebcamActive ? 'var(--accent-green)' : 'var(--accent-cyan)'}`
          }}>
            <Camera size={22} color={isWebcamActive ? 'var(--accent-green)' : 'var(--accent-cyan)'} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 800 }}>Real-Time Surveillance Stream</h2>
              {activeThreat ? (
                <span className="badge badge-critical pulse-alert">
                  <AlertTriangle size={12} /> THREAT: {activeThreat.toUpperCase()}
                </span>
              ) : isWebcamActive ? (
                <span className="badge badge-normal">
                  <ShieldCheck size={12} /> FEED ACTIVE
                </span>
              ) : (
                <span className="badge badge-cyan">STANDBY</span>
              )}
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Hardware-Accelerated YOLOv5 Inference Loop • Powered by RTX 3050 GPU
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {/* Webcam Toggle Button */}
          {!isWebcamActive ? (
            <button
              onClick={startWebcam}
              className="btn btn-primary"
              style={{ fontSize: '0.85rem', padding: '8px 14px' }}
            >
              <Video size={16} /> Start Live Webcam
            </button>
          ) : (
            <button
              onClick={stopWebcam}
              className="btn btn-danger"
              style={{ fontSize: '0.85rem', padding: '8px 14px' }}
            >
              <VideoOff size={16} /> Stop Camera
            </button>
          )}

          {/* AI Bounding Boxes Toggle */}
          <button
            onClick={() => setShowOverlay(!showOverlay)}
            className={`btn ${showOverlay ? 'btn-primary' : 'btn-ghost'}`}
            style={{ fontSize: '0.8rem', padding: '8px 12px' }}
          >
            <Cpu size={14} /> Boxes: {showOverlay ? 'ON' : 'OFF'}
          </button>

          {/* Confidence Threshold Slider */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(0,0,0,0.35)',
            padding: '6px 12px',
            borderRadius: '8px',
            border: '1px solid var(--border-color)',
          }}>
            <Sliders size={14} color="var(--accent-cyan)" />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Conf:</span>
            <input
              type="range"
              min="0.15"
              max="0.85"
              step="0.05"
              value={confThreshold}
              onChange={(e) => setConfThreshold(parseFloat(e.target.value))}
              style={{ width: '85px', accentColor: 'var(--accent-cyan)' }}
            />
            <span style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-cyan)' }}>
              {(confThreshold * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>

      {webcamError && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          color: '#fca5a5',
          padding: '12px 16px',
          borderRadius: '8px',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}>
          <AlertTriangle size={16} /> {webcamError}
        </div>
      )}

      {/* Main Video Viewport */}
      <div style={{
        position: 'relative',
        width: '100%',
        borderRadius: '10px',
        overflow: 'hidden',
        border: '1px solid rgba(255, 255, 255, 0.12)',
        background: '#070a14',
        minHeight: '440px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        {/* Hidden Video element for WebRTC ingestion */}
        <video ref={videoRef} playsInline muted style={{ display: 'none' }} />

        {/* Render Canvas */}
        <canvas
          ref={canvasRef}
          style={{
            width: '100%',
            height: 'auto',
            maxHeight: '70vh',
            display: isWebcamActive ? 'block' : 'none',
            objectFit: 'contain',
          }}
        />

        {/* Standby Placeholder when Webcam is Off */}
        {!isWebcamActive && (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '60px 20px',
            textAlign: 'center',
            gap: '16px',
          }}>
            <div style={{
              width: '80px',
              height: '80px',
              borderRadius: '50%',
              background: 'rgba(0, 229, 255, 0.08)',
              border: '2px solid rgba(0, 229, 255, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 30px rgba(0, 229, 255, 0.2)',
            }}>
              <Camera size={38} color="var(--accent-cyan)" />
            </div>
            <div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: '6px' }}>
                Live Weapon Detection Camera Offline
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', maxWidth: '480px', lineHeight: 1.6 }}>
                Click <strong>"Start Live Webcam"</strong> to begin real-time surveillance streaming with instantaneous AI bounding boxes, threat detection, and audio siren warnings.
              </p>
            </div>
            <button
              onClick={startWebcam}
              className="btn btn-primary"
              style={{ padding: '10px 20px', fontSize: '0.9rem', fontWeight: 700 }}
            >
              <Video size={18} /> Launch Real-Time Webcam Stream
            </button>
          </div>
        )}
      </div>

      {/* Detection Feed Telemetry Bar */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '12px',
        padding: '12px',
        background: 'rgba(0,0,0,0.3)',
        borderRadius: '8px',
        border: '1px solid var(--border-color)',
      }}>
        <div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>STREAM STATUS</div>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: isWebcamActive ? 'var(--accent-green)' : 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
            {isWebcamActive ? '● STREAMING (ONLINE)' : '○ IDLE (OFFLINE)'}
          </div>
        </div>

        <div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>THREATS DETECTED</div>
          <div style={{ fontSize: '0.95rem', fontWeight: 800, color: activeThreat ? '#ef4444' : 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>
            {activeThreat ? `🚨 ${activeThreat.toUpperCase()}` : 'SHIELD SECURE'}
          </div>
        </div>

        <div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>INFERENCE LATENCY</div>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
            {latencyMs.toFixed(1)} ms / frame
          </div>
        </div>

        <div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>ACTIVE FPS</div>
          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>
            {fps.toFixed(1)} FPS
          </div>
        </div>
      </div>
    </div>
  );
};
