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

let mockState: SystemStatus["state"] = "running";

const now = new Date();

export const mockStatus = (): SystemStatus => ({
  state: mockState,
  analyzerMode: "rule",
  detectorEnabled: true,
  latestMessageAt: now.toISOString(),
  queueDepth: 1,
  uptimeSeconds: 4821,
});

export const mockMessages = (): ChatMessage[] => [
  {
    id: "m1",
    senderRole: "other",
    text: "今晚要不要一起吃饭？",
    timestamp: new Date(now.getTime() - 35_000).toISOString(),
    source: "yolo_ocr",
    confidence: 0.97,
  },
  {
    id: "m2",
    senderRole: "me",
    text: "可以，我 7 点后有空。",
    timestamp: new Date(now.getTime() - 26_000).toISOString(),
    source: "manual",
    confidence: 1,
  },
  {
    id: "m3",
    senderRole: "other",
    text: "那就老地方见。",
    timestamp: new Date(now.getTime() - 10_000).toISOString(),
    source: "yolo_ocr",
    confidence: 0.93,
  },
];

export const mockContext = (): CurrentContext => ({
  chatKey: "张三[wxid_demo]",
  recentMessages: mockMessages(),
  replyCandidate: {
    id: "m3",
    senderRole: "other",
    text: "那就老地方见。",
    timestamp: new Date(now.getTime() - 10_000).toISOString(),
    source: "yolo_ocr",
    confidence: 0.93,
  },
});

export const mockDetections = (): DetectionPayload => ({
  capturedAt: now.toISOString(),
  imageUrl: "https://placehold.co/960x540/e8eefc/1f2a44?text=Detection+Preview",
  detections: [
    {
      id: "d1",
      label: "bubble_other",
      confidence: 0.95,
      bbox: [26, 110, 470, 210],
      ocrText: "今晚要不要一起吃饭？",
    },
    {
      id: "d2",
      label: "bubble_me",
      confidence: 0.9,
      bbox: [430, 230, 915, 315],
      ocrText: "可以，我 7 点后有空。",
    },
  ],
});

export const mockMemories = (): MemoryItem[] => [
  {
    id: "mem1",
    owner: "other",
    type: "preference",
    content: "喜欢晚上 7 点后约饭",
    createdAt: new Date(now.getTime() - 86_000).toISOString(),
    confidence: 0.86,
  },
  {
    id: "mem2",
    owner: "other",
    type: "topic",
    content: "近期常聊工作排期",
    createdAt: new Date(now.getTime() - 38_000).toISOString(),
    confidence: 0.8,
  },
];

let mockSettingsData: SettingsData = {
  analyzerMode: "rule",
  useYoloDetector: true,
  yoloConfThreshold: 0.25,
  yoloIouThreshold: 0.45,
  replyMaxLength: 160,
};

export const mockSettings = (): SettingsData => ({ ...mockSettingsData });

export const mockLogs = (): LogItem[] => [
  {
    id: "l1",
    level: "INFO",
    message: "Listening for new messages... analyzer_mode=rule",
    timestamp: new Date(now.getTime() - 55_000).toISOString(),
  },
  {
    id: "l2",
    level: "INFO",
    message: "Received message: 今晚要不要一起吃饭？ intent=question conf=0.92",
    timestamp: new Date(now.getTime() - 20_000).toISOString(),
  },
  {
    id: "l3",
    level: "DEBUG",
    message: "parse_source=yolo_ocr detections=2",
    timestamp: new Date(now.getTime() - 18_000).toISOString(),
  },
];

export const applyMockSettings = (next: SettingsData): SettingsData => {
  mockSettingsData = { ...next };
  return mockSettings();
};

export const mockStart = (): ControlResponse => {
  mockState = "running";
  return { accepted: true, state: mockState };
};

export const mockStop = (): ControlResponse => {
  mockState = "stopped";
  return { accepted: true, state: mockState };
};
