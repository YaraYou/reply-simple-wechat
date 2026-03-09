import type { DetectionResult } from "../../types";

interface DetectionTableProps {
  rows: DetectionResult[];
  selectedId?: string;
  onSelect?: (id: string) => void;
}

export function DetectionTable({ rows, selectedId, onSelect }: DetectionTableProps) {
  return (
    <section className="card detection-table">
      <h3>Detection Table</h3>
      <table>
        <thead>
          <tr>
            <th>Label</th>
            <th>Confidence</th>
            <th>BBox</th>
            <th>OCR</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.id}
              className={selectedId === row.id ? "selected-row" : ""}
              onClick={() => onSelect?.(row.id)}
            >
              <td>{row.label}</td>
              <td>{Math.round(row.confidence * 100)}%</td>
              <td>{row.bbox.join(", ")}</td>
              <td>{row.ocrText}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
