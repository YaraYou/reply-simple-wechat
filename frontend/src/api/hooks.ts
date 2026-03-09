import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./endpoints";
import type { SettingsData } from "../types";

export const queryKeys = {
  status: ["status"] as const,
  messagesRecent: ["messages", "recent"] as const,
  contextCurrent: ["context", "current"] as const,
  detectionsLatest: ["detections", "latest"] as const,
  memories: ["memories"] as const,
  settings: ["settings"] as const,
  logs: ["logs"] as const,
};

export const useStatusQuery = () =>
  useQuery({
    queryKey: queryKeys.status,
    queryFn: api.getStatus,
    refetchInterval: 5000,
    refetchIntervalInBackground: false,
  });

export const useRecentMessagesQuery = () =>
  useQuery({
    queryKey: queryKeys.messagesRecent,
    queryFn: api.getRecentMessages,
    refetchInterval: 2000,
    refetchIntervalInBackground: false,
  });

export const useCurrentContextQuery = () =>
  useQuery({
    queryKey: queryKeys.contextCurrent,
    queryFn: api.getCurrentContext,
    refetchInterval: 2000,
    refetchIntervalInBackground: false,
  });

export const useDetectionsLatestQuery = () =>
  useQuery({
    queryKey: queryKeys.detectionsLatest,
    queryFn: api.getLatestDetections,
    refetchInterval: 3000,
    refetchIntervalInBackground: false,
  });

export const useMemoriesQuery = () =>
  useQuery({
    queryKey: queryKeys.memories,
    queryFn: api.getMemories,
  });

export const useSettingsQuery = () =>
  useQuery({
    queryKey: queryKeys.settings,
    queryFn: api.getSettings,
  });

export const useLogsQuery = () =>
  useQuery({
    queryKey: queryKeys.logs,
    queryFn: api.getLogs,
    refetchInterval: 3000,
    refetchIntervalInBackground: false,
  });

export const useStartMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.start,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.status });
      await queryClient.invalidateQueries({ queryKey: queryKeys.messagesRecent });
      await queryClient.invalidateQueries({ queryKey: queryKeys.contextCurrent });
    },
  });
};

export const useStopMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.stop,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.status });
    },
  });
};

export const useSaveSettingsMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SettingsData) => api.postSettings(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.settings });
      await queryClient.invalidateQueries({ queryKey: queryKeys.status });
    },
  });
};
