export type BotRunState = "running" | "stopped" | "starting" | "stopping";

export interface SystemStatus {
  state: BotRunState;
  analyzerMode: "rule" | "ml";
  detectorEnabled: boolean;
  latestMessageAt: string;
  queueDepth: number;
  uptimeSeconds: number;
}

export interface ChatMessage {
  id: string;
  senderRole: "me" | "other" | "system";
  text: string;
  timestamp: string;
  source: "yolo_ocr" | "ocr_fallback" | "manual";
  confidence: number;
}

export interface CurrentContext {
  chatKey: string;
  recentMessages: ChatMessage[];
  replyCandidate?: ChatMessage;
}

export interface DetectionResult {
  id: string;
  label: "bubble_other" | "bubble_me" | "timestamp" | "system_tip";
  confidence: number;
  bbox: [number, number, number, number];
  ocrText: string;
}

export interface DetectionPayload {
  capturedAt: string;
  imageUrl: string;
  detections: DetectionResult[];
}

export interface MemoryItem {
  id: string;
  owner: "other" | "me";
  type: "preference" | "taboo" | "plan" | "promise" | "topic";
  content: string;
  createdAt: string;
  confidence: number;
}

export interface SettingsData {
  analyzerMode: "rule" | "ml";
  useYoloDetector: boolean;
  yoloConfThreshold: number;
  yoloIouThreshold: number;
  replyMaxLength: number;
}

export interface LogItem {
  id: string;
  level: "DEBUG" | "INFO" | "WARNING" | "ERROR";
  message: string;
  timestamp: string;
}

export interface ControlResponse {
  accepted: boolean;
  state: BotRunState;
}
