import React from 'react';
import { HardDrive, FileText, Database, Terminal, Layers, CheckCircle } from 'lucide-react';

export const DatasetPanel: React.FC = () => {
  const yamlConfig = `train: data_downloaded/train/images
val: data_downloaded/valid/images
test: data_downloaded/test/images

nc: 3
names: ['gun', 'heavy-weapon', 'knife']`;

  const exportCommands = `# 1. Train YOLOv5 custom model on GPU
python src/train_custom.py --data data/data.yaml --weights yolov5s.pt --epochs 100 --img 640

# 2. Evaluate model performance & export metrics
python src/evaluate.py --weights models/best.pt --data data/data.yaml

# 3. Export to INT8 Quantized TFLite format for Raspberry Pi
python yolov5/export.py --weights models/best.pt --include tflite --int8 --img 640

# 4. Deploy edge surveillance loop on Raspberry Pi
python src/detect_tflite.py --model models/best.tflite --source 0`;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Overview Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
        <div className="glass-panel" style={{ padding: '16px', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ background: 'rgba(0, 229, 255, 0.15)', padding: '12px', borderRadius: '10px' }}>
            <Database size={24} color="var(--accent-cyan)" />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Dataset Structure</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-main)' }}>PyTorch YOLOv5 Format</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)' }}>train / val / test split</div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '16px', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ background: 'rgba(16, 185, 129, 0.15)', padding: '12px', borderRadius: '10px' }}>
            <Layers size={24} color="var(--accent-green)" />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Target Crime Classes</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--accent-green)' }}>3 Custom Classes</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>gun, knife, heavy-weapon</div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '16px', display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ background: 'rgba(139, 92, 246, 0.15)', padding: '12px', borderRadius: '10px' }}>
            <HardDrive size={24} color="var(--accent-purple)" />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Weights Location</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>models/best.pt</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>models/best.tflite</div>
          </div>
        </div>
      </div>

      {/* Code Snippets & YAML Preview */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '20px' }}>
        {/* data.yaml */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileText size={18} color="var(--accent-cyan)" />
              <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>data/data.yaml Dataset Configuration</h3>
            </div>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>data/data.yaml</span>
          </div>

          <pre style={{
            background: 'rgba(0,0,0,0.5)',
            padding: '14px',
            borderRadius: '8px',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.85rem',
            color: '#7dd3fc',
            border: '1px solid var(--border-color)',
            overflowX: 'auto'
          }}>
            {yamlConfig}
          </pre>
        </div>

        {/* Execution Workflow Commands */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Terminal size={18} color="var(--accent-green)" />
              <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>Training & Edge Export Pipeline</h3>
            </div>
            <span className="badge badge-normal"><CheckCircle size={10} strokeWidth={3} /> Pipeline Ready</span>
          </div>

          <pre style={{
            background: 'rgba(0,0,0,0.5)',
            padding: '14px',
            borderRadius: '8px',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.8rem',
            color: '#a7f3d0',
            border: '1px solid var(--border-color)',
            overflowX: 'auto',
            whiteSpace: 'pre-wrap',
          }}>
            {exportCommands}
          </pre>
        </div>
      </div>
    </div>
  );
};
