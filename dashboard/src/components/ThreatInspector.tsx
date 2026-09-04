import React, { useState, useEffect } from 'react';
import type { InferenceResult, SampleItem } from '../types';
import { Upload, Crosshair, AlertTriangle, ShieldCheck, Download, Zap, Image as ImageIcon } from 'lucide-react';
import { alarmAudio } from '../utils/audio';

interface ThreatInspectorProps {
  confThreshold: number;
  soundEnabled: boolean;
  onThreatDetected?: () => void;
}

export const ThreatInspector: React.FC<ThreatInspectorProps> = ({
  confThreshold,
  soundEnabled,
  onThreatDetected,
}) => {
  const [samples, setSamples] = useState<SampleItem[]>([]);
  const [selectedSample, setSelectedSample] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<InferenceResult | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Fetch sample images list
  useEffect(() => {
    fetch('/api/samples')
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setSamples(data);
          // Auto-select first sample for instant showcase
          if (data.length > 0) {
            handleRunSample(data[0].filename);
          }
        }
      })
      .catch((err) => console.warn('Could not fetch samples:', err));
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setErrorMsg(null);
    setLoading(true);
    setSelectedSample(null);

    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('conf', confThreshold.toString());
    formData.append('iou', '0.45');
    formData.append('camera_id', 'INSPECTOR_UPLOAD');

    try {
      const res = await fetch('/api/detect/upload', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error(`Inference failed: ${res.statusText}`);
      const data: InferenceResult = await res.json();
      setResult(data);

      if (data.threat_detected) {
        if (soundEnabled) alarmAudio.playSecuritySiren();
        if (onThreatDetected) onThreatDetected();
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Detection failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRunSample = async (filename: string) => {
    setErrorMsg(null);
    setSelectedSample(filename);
    setLoading(true);
    setPreviewUrl(`/api/samples/${filename}`);

    try {
      const res = await fetch(`/api/detect/sample/${filename}?conf=${confThreshold}&iou=0.45`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error(`Sample analysis failed: ${res.statusText}`);
      const data: InferenceResult = await res.json();
      setResult(data);

      if (data.threat_detected) {
        if (soundEnabled) alarmAudio.playSecuritySiren();
        if (onThreatDetected) onThreatDetected();
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Analysis error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Banner */}
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ background: 'rgba(0, 229, 255, 0.15)', padding: '10px', borderRadius: '10px' }}>
            <Crosshair size={24} color="var(--accent-cyan)" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>Weapon & Threat Inspector</h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Upload any security image/video frame or pick a benchmark sample to run instant YOLOv5 GPU inference
            </p>
          </div>
        </div>

        {/* Upload Button */}
        <label className="btn btn-primary" style={{ cursor: 'pointer', padding: '10px 18px' }}>
          <Upload size={16} /> Upload Test Image
          <input type="file" accept="image/*" onChange={handleFileUpload} style={{ display: 'none' }} />
        </label>
      </div>

      {/* Benchmark Samples Selector */}
      {samples.length > 0 && (
        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Zap size={16} color="var(--accent-warning)" />
            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-main)' }}>
              One-Click Benchmark Samples:
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>(Curated from validation set)</span>
          </div>

          <div style={{ display: 'flex', gap: '10px', overflowX: 'auto', paddingBottom: '6px' }}>
            {samples.map((s) => {
              const isSelected = selectedSample === s.filename;
              const isGun = s.label === 'gun';
              const isKnife = s.label === 'knife';
              const isHeavy = s.label === 'heavy-weapon';

              return (
                <button
                  key={s.filename}
                  onClick={() => handleRunSample(s.filename)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    background: isSelected ? 'rgba(0, 229, 255, 0.15)' : 'rgba(255,255,255,0.03)',
                    border: `1px solid ${isSelected ? 'var(--accent-cyan)' : 'var(--border-color)'}`,
                    color: 'var(--text-main)',
                    cursor: 'pointer',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <span style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    background: isGun ? '#ef4444' : isKnife ? '#f59e0b' : isHeavy ? '#8b5cf6' : '#10b981',
                  }} />
                  {s.label.toUpperCase()} ({s.filename.replace('sample_', '').replace('.jpg', '')})
                </button>
              );
            })}
          </div>
        </div>
      )}

      {errorMsg && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          color: '#fca5a5',
          padding: '12px 16px',
          borderRadius: '8px',
          fontSize: '0.85rem',
        }}>
          ⚠️ {errorMsg}
        </div>
      )}

      {/* Main Analysis Viewport */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
        {/* Visualizer Card */}
        <div className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ImageIcon size={18} color="var(--accent-cyan)" />
              <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>Annotated Visual Evidence</h3>
            </div>
            {result?.snapshot_url && (
              <a
                href={result.annotated_image}
                download={`evidence_${result.filename || 'detection'}.jpg`}
                className="btn btn-ghost"
                style={{ fontSize: '0.75rem', padding: '4px 10px' }}
              >
                <Download size={14} /> Download Image
              </a>
            )}
          </div>

          <div style={{
            position: 'relative',
            width: '100%',
            minHeight: '360px',
            background: '#070a14',
            borderRadius: '8px',
            overflow: 'hidden',
            border: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            {loading ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  border: '3px solid rgba(0,229,255,0.2)',
                  borderTopColor: 'var(--accent-cyan)',
                  borderRadius: '50%',
                  animation: 'spin 0.8s linear infinite',
                }} />
                <span style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
                  Executing YOLO GPU Inference...
                </span>
              </div>
            ) : result?.annotated_image ? (
              <img
                src={result.annotated_image}
                alt="Detection output"
                style={{ width: '100%', height: 'auto', maxHeight: '550px', objectFit: 'contain', display: 'block' }}
              />
            ) : previewUrl ? (
              <img
                src={previewUrl}
                alt="Original preview"
                style={{ width: '100%', height: 'auto', maxHeight: '550px', objectFit: 'contain', display: 'block' }}
              />
            ) : (
              <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
                <Upload size={36} color="var(--text-dim)" style={{ marginBottom: '10px' }} />
                <p style={{ fontSize: '0.85rem' }}>Select a benchmark sample or upload an image to view annotations.</p>
              </div>
            )}
          </div>
        </div>

        {/* Detections & Metrics Card */}
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>Inference Breakdown</h3>
            {result?.threat_detected ? (
              <span className="badge badge-critical pulse-alert">
                <AlertTriangle size={12} /> WEAPON DETECTED
              </span>
            ) : result ? (
              <span className="badge badge-normal">
                <ShieldCheck size={12} /> CLEAR / NO THREAT
              </span>
            ) : null}
          </div>

          {result && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div style={{ background: 'rgba(0,0,0,0.35)', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>GPU Latency</span>
                <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
                  {result.inference_ms} ms
                </div>
              </div>

              <div style={{ background: 'rgba(0,0,0,0.35)', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Objects Found</span>
                <div style={{ fontSize: '1.2rem', fontWeight: 800, color: result.detections.length > 0 ? '#ef4444' : 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>
                  {result.detections.length}
                </div>
              </div>
            </div>
          )}

          {/* Detections List */}
          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Identified Bounding Boxes:
            </span>

            {result?.detections && result.detections.length > 0 ? (
              result.detections.map((det, i) => (
                <div
                  key={i}
                  style={{
                    background: 'rgba(255,255,255,0.03)',
                    border: `1px solid ${det.isThreat ? 'rgba(239, 68, 68, 0.4)' : 'var(--border-color)'}`,
                    borderRadius: '8px',
                    padding: '12px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{
                      fontWeight: 800,
                      color: det.isThreat ? '#ef4444' : '#10b981',
                      fontSize: '0.9rem',
                      textTransform: 'uppercase',
                      fontFamily: 'var(--font-mono)'
                    }}>
                      🚨 {det.label}
                    </span>
                    <span className={`badge ${det.severity === 'CRITICAL' ? 'badge-critical' : 'badge-high'}`}>
                      {det.severity}
                    </span>
                  </div>

                  {/* Confidence Bar */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '4px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Confidence:</span>
                      <strong style={{ fontFamily: 'var(--font-mono)' }}>{(det.confidence * 100).toFixed(1)}%</strong>
                    </div>
                    <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${det.confidence * 100}%`,
                          height: '100%',
                          background: det.isThreat ? 'linear-gradient(90deg, #f59e0b, #ef4444)' : '#10b981',
                        }}
                      />
                    </div>
                  </div>

                  {/* Coordinates */}
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                    BBOX: [{det.bbox.join(', ')}]
                  </div>
                </div>
              ))
            ) : (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                {result ? 'No target classes detected above confidence threshold.' : 'No media analyzed yet.'}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
