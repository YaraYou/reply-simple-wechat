import {
  applyMockSettings,
  mockContext,
  mockDetections,
  mockLogs,
  mockMemories,
  mockMessages,
  mockSettings,
  mockStart,
  mockStatus,
  mockStop,
} from "./data";
import type { ControlResponse, SettingsData } from "../types";

const delay = async (ms = 120): Promise<void> => {
  await new Promise((resolve) => setTimeout(resolve, ms));
};

export const mockGetStatus = async () => {
  await delay();
  return mockStatus();
};

export const mockGetRecentMessages = async () => {
  await delay();
  return mockMessages();
};

export const mockGetCurrentContext = async () => {
  await delay();
  return mockContext();
};

export const mockGetLatestDetections = async () => {
  await delay();
  return mockDetections();
};

export const mockGetMemories = async () => {
  await delay();
  return mockMemories();
};

export const mockGetSettings = async () => {
  await delay();
  return mockSettings();
};

export const mockPostSettings = async (payload: SettingsData) => {
  await delay();
  return applyMockSettings(payload);
};

export const mockGetLogs = async () => {
  await delay();
  return mockLogs();
};

export const mockStartControl = async (): Promise<ControlResponse> => {
  await delay();
  return mockStart();
};

export const mockStopControl = async (): Promise<ControlResponse> => {
  await delay();
  return mockStop();
};
