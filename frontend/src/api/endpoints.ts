import { apiConfig } from "./config";
import { getJson, postJson } from "./client";
import {
  mockGetCurrentContext,
  mockGetLatestDetections,
  mockGetLogs,
  mockGetMemories,
  mockGetRecentMessages,
  mockGetSettings,
  mockGetStatus,
  mockPostSettings,
  mockStartControl,
  mockStopControl,
} from "../mocks/handlers";
import type {
  ChatMessage,
  ControlResponse,
  CurrentContext,
  DetectionPayload,
  LogItem,
  MemoryItem,
  SettingsData,
  SystemStatus,
} from "../types";

export const api = {
  getStatus: (): Promise<SystemStatus> =>
    apiConfig.useMock ? mockGetStatus() : getJson<SystemStatus>("/api/status"),

  getRecentMessages: (): Promise<ChatMessage[]> =>
    apiConfig.useMock
      ? mockGetRecentMessages()
      : getJson<ChatMessage[]>("/api/messages/recent"),

  getCurrentContext: (): Promise<CurrentContext> =>
    apiConfig.useMock
      ? mockGetCurrentContext()
      : getJson<CurrentContext>("/api/context/current"),

  getLatestDetections: (): Promise<DetectionPayload> =>
    apiConfig.useMock
      ? mockGetLatestDetections()
      : getJson<DetectionPayload>("/api/detections/latest"),

  getMemories: (): Promise<MemoryItem[]> =>
    apiConfig.useMock
      ? mockGetMemories()
      : getJson<MemoryItem[]>("/api/memories"),

  getSettings: (): Promise<SettingsData> =>
    apiConfig.useMock
      ? mockGetSettings()
      : getJson<SettingsData>("/api/settings"),

  postSettings: (payload: SettingsData): Promise<SettingsData> =>
    apiConfig.useMock
      ? mockPostSettings(payload)
      : postJson<SettingsData, SettingsData>("/api/settings", payload),

  getLogs: (): Promise<LogItem[]> =>
    apiConfig.useMock ? mockGetLogs() : getJson<LogItem[]>("/api/logs"),

  start: (): Promise<ControlResponse> =>
    apiConfig.useMock
      ? mockStartControl()
      : postJson<ControlResponse, never>("/api/control/start"),

  stop: (): Promise<ControlResponse> =>
    apiConfig.useMock
      ? mockStopControl()
      : postJson<ControlResponse, never>("/api/control/stop"),
};
