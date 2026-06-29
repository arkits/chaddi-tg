import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

export interface Group {
  group_id: string;
  name: string;
  created: string;
  updated: string;
  metadata?: Record<string, unknown>;
}

export interface GroupsResponse {
  current_page: number;
  total_groups: number;
  total_pages: number;
  groups: Group[];
}

export interface GroupMessage {
  message_id: string;
  text: string;
  time_sent: string;
  update?: string;
  from_bakchod: {
    tg_id: string;
    username: string | null;
    pretty_name: string | null;
  };
}

export interface GroupMessagesResponse {
  current_page: number;
  total_pages: number;
  total_messages: number;
  messages: GroupMessage[];
}

export interface GroupMember {
  tg_id: string;
  username: string | null;
  pretty_name: string | null;
  rokda: number;
  lastseen: string | null;
}

export interface GroupMembersResponse {
  members: GroupMember[];
  total: number;
}

export function useGroups(pageNumber: number = 1) {
  return useQuery({
    queryKey: ["groups", pageNumber],
    queryFn: () =>
      api.get<GroupsResponse>(`/api/groups?page_number=${pageNumber}`),
  });
}

export function useGroup(groupId: string) {
  return useQuery({
    queryKey: ["groups", groupId],
    queryFn: () => api.get<Group>(`/api/groups/${groupId}`),
    enabled: !!groupId,
  });
}

export function useGroupMessages(
  groupId: string,
  pageNumber: number = 1,
  includeUpdate: boolean = false
) {
  return useQuery({
    queryKey: ["groups", groupId, "messages", pageNumber, includeUpdate],
    queryFn: () =>
      api.get<GroupMessagesResponse>(
        `/api/groups/${groupId}/messages?page_number=${pageNumber}&include_update=${includeUpdate}`
      ),
    enabled: !!groupId,
  });
}

export function useGroupMembers(groupId: string) {
  return useQuery({
    queryKey: ["groups", groupId, "members"],
    queryFn: () =>
      api.get<GroupMembersResponse>(`/api/groups/${groupId}/members`),
    enabled: !!groupId,
  });
}

export function useSetGroupMetadata() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      groupId,
      metadata,
    }: {
      groupId: string;
      metadata: string;
    }) =>
      api.post("/api/group/metadata", {
        group_id: groupId,
        metadata,
      }),
    onSuccess: (_, { groupId }) => {
      queryClient.invalidateQueries({ queryKey: ["groups", groupId] });
    },
  });
}

export function useSendMessageToGroup() {
  return useMutation({
    mutationFn: ({
      groupId,
      message,
    }: {
      groupId: string;
      message: string;
    }) => api.post(`/api/groups/${groupId}/send-message`, { message }),
  });
}
