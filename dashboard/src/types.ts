export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  confidence: number;
  isThreat: boolean;
}

export interface ThreatAlert {
  id: string;
  timestamp: string;
  epoch: number;
  cameraId: string;
  locationName: string;
  threatClass: 'gun' | 'knife' | 'heavy-weapon' | 'suspicious-package' | 'unusual-activity';
  confidence: number;
  severity: Severity;
  snapshotUrl?: string;
  status: 'ACTIVE' | 'ACKNOWLEDGED' | 'DISPATCHED' | 'FALSE_ALARM';
  boundingBoxes?: BoundingBox[];
}

export interface CameraFeed {
  id: string;
  name: string;
  location: string;
  status: 'ONLINE' | 'OFFLINE' | 'ALERT';
  resolution: string;
  fps: number;
  deviceType: 'RTSP IP Camera' | 'Raspberry Pi Edge' | 'USB WebCam';
  latencyMs: number;
  threatCount24h: number;
}

export interface ModelMetric {
  className: string;
  precision: number;
  recall: number;
  map50: number;
  map50_95: number;
  sampleCount: number;
}

export interface EdgeNodeTelemetry {
  nodeId: string;
  nodeName: string;
  hardware: string;
  cpuTempC: number;
  cpuUsagePct: number;
  ramUsagePct: number;
  inferenceEngine: string;
  quantization: string;
  avgLatencyMs: number;
  status: 'OPTIMAL' | 'WARM' | 'OVERLOAD';
}
