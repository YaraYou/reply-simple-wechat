interface DetectionImagePanelProps {
  imageUrl: string;
  capturedAt: string;
}

export function DetectionImagePanel({ imageUrl, capturedAt }: DetectionImagePanelProps) {
  return (
    <section className="card detection-image-panel">
      <h3>Detection Snapshot</h3>
      <p>{new Date(capturedAt).toLocaleString()}</p>
      <img src={imageUrl} alt="Latest detection" className="detection-image" />
    </section>
  );
}
