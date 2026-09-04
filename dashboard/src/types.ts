export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export interface DetectionBox {
  bbox: [number, number, number, number]; // [x1, y1, x2, y2]
  label: string;
  confidence: number;
  isThreat: boolean;
  severity: Severity;
}

export type BoundingBox = DetectionBox;

export interface ThreatAlert {
  id: string;
  event_id?: string;
  timestamp: string;
  epoch: number;
  cameraId: string;
  locationName?: string;
  threatClass: string;
  confidence: number;
  severity: Severity;
  snapshotUrl?: string | null;
  snapshot_path?: string;
  status: 'ACTIVE' | 'ACKNOWLEDGED' | 'DISPATCHED' | 'FALSE_ALARM' | 'RESOLVED';
  bbox?: [number, number, number, number];
}

export interface CameraFeed {
  id: string;
  name: string;
  location: string;
  status: 'ONLINE' | 'OFFLINE' | 'ALERT';
  resolution: string;
  fps: number;
  deviceType: 'Webcam' | 'RTSP IP Camera' | 'Raspberry Pi Edge' | 'Video File';
  latencyMs: number;
}

export interface TelemetryData {
  cpu_usage_pct: number;
  ram_usage_pct: number;
  ram_used_gb: number;
  ram_total_gb: number;
  vram_used_mb: number;
  vram_total_mb: number;
  gpu_temp_c: number;
  gpu_name: string;
  cuda_active: boolean;
}

export interface SampleItem {
  filename: string;
  label: string;
  url: string;
}

export interface InferenceResult {
  success: boolean;
  threat_detected: boolean;
  top_threat: string | null;
  detections: DetectionBox[];
  inference_ms: number;
  annotated_image: string;
  snapshot_url?: string | null;
  filename?: string;
}

export interface EvaluationMetrics {
  model_weights?: string;
  overall_precision: number;
  overall_recall: number;
  mAP_50: number;
  mAP_50_95: number;
  inference_speed_ms?: number;
  classes: Record<string, {
    precision: number;
    recall: number;
    map50: number;
    map50_95: number;
  }>;
}
