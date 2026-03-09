import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "../layouts/AppLayout";
import { ChatMonitorPage } from "../pages/ChatMonitorPage";
import { DashboardPage } from "../pages/DashboardPage";
import { DetectionDebugPage } from "../pages/DetectionDebugPage";
import { LogsPage } from "../pages/LogsPage";
import { MemoryCenterPage } from "../pages/MemoryCenterPage";
import { SettingsPage } from "../pages/SettingsPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/chat-monitor" element={<ChatMonitorPage />} />
        <Route path="/detection-debug" element={<DetectionDebugPage />} />
        <Route path="/memory-center" element={<MemoryCenterPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/logs" element={<LogsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
