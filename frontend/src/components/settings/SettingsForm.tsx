import { useEffect, useState } from "react";
import type { SettingsData } from "../../types";

interface SettingsFormProps {
  data: SettingsData;
  onSubmit: (payload: SettingsData) => void;
  saving: boolean;
}

export function SettingsForm({ data, onSubmit, saving }: SettingsFormProps) {
  const [form, setForm] = useState<SettingsData>(data);

  useEffect(() => {
    setForm(data);
  }, [data]);

  return (
    <form
      className="card settings-form"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(form);
      }}
    >
      <h3>Settings</h3>

      <label>
        Analyzer Mode
        <select
          value={form.analyzerMode}
          onChange={(e) =>
            setForm((prev) => ({ ...prev, analyzerMode: e.target.value as SettingsData["analyzerMode"] }))
          }
        >
          <option value="rule">rule</option>
          <option value="ml">ml</option>
        </select>
      </label>

      <label>
        Use YOLO Detector
        <input
          type="checkbox"
          checked={form.useYoloDetector}
          onChange={(e) => setForm((prev) => ({ ...prev, useYoloDetector: e.target.checked }))}
        />
      </label>

      <label>
        YOLO Conf Threshold
        <input
          type="number"
          step="0.01"
          value={form.yoloConfThreshold}
          onChange={(e) => setForm((prev) => ({ ...prev, yoloConfThreshold: Number(e.target.value) }))}
        />
      </label>

      <label>
        YOLO IoU Threshold
        <input
          type="number"
          step="0.01"
          value={form.yoloIouThreshold}
          onChange={(e) => setForm((prev) => ({ ...prev, yoloIouThreshold: Number(e.target.value) }))}
        />
      </label>

      <label>
        Reply Max Length
        <input
          type="number"
          value={form.replyMaxLength}
          onChange={(e) => setForm((prev) => ({ ...prev, replyMaxLength: Number(e.target.value) }))}
        />
      </label>

      <button type="submit" disabled={saving}>
        {saving ? "Saving..." : "Save Settings"}
      </button>
    </form>
  );
}
