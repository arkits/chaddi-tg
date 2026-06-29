import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import {
  useGroups,
  useGroupMessages,
  useSendMessageToGroup,
  type Group,
} from "@/hooks/use-groups";
import { formatDate } from "@/lib/utils";

export default function Messenger() {
  const [searchParams, setSearchParams] = useSearchParams();
  const deeplinkGroupId = searchParams.get("group_id");

  const [groupsPage, setGroupsPage] = useState(1);
  const [allGroups, setAllGroups] = useState<Group[]>([]);
  const [hasMoreGroups, setHasMoreGroups] = useState(true);
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(
    deeplinkGroupId
  );
  const [messageText, setMessageText] = useState("");
  const [groupSearch, setGroupSearch] = useState("");
  const [messagesPage, setMessagesPage] = useState(1);

  const groupsListRef = useRef<HTMLDivElement>(null);
  const deeplinkResolvedRef = useRef(false);

  const { data: groupsPageData, isLoading: groupsLoading } = useGroups(groupsPage);
  const { data: messages, isLoading: messagesLoading } = useGroupMessages(
    selectedGroupId ?? "",
    messagesPage
  );
  const sendMessage = useSendMessageToGroup();

  useEffect(() => {
    if (!groupsPageData?.groups) {
      return;
    }

    setAllGroups((previous) => {
      const existingIds = new Set(previous.map((group) => group.group_id));
      const newGroups = groupsPageData.groups.filter(
        (group) => !existingIds.has(group.group_id)
      );
      return [...previous, ...newGroups];
    });
    setHasMoreGroups(groupsPageData.current_page < groupsPageData.total_pages);
  }, [groupsPageData]);

  useEffect(() => {
    if (!deeplinkGroupId || deeplinkResolvedRef.current) {
      return;
    }

    const found = allGroups.some((group) => group.group_id === deeplinkGroupId);
    if (found) {
      setSelectedGroupId(deeplinkGroupId);
      deeplinkResolvedRef.current = true;
      return;
    }

    if (!groupsLoading && hasMoreGroups) {
      setGroupsPage((page) => page + 1);
    }
  }, [deeplinkGroupId, allGroups, groupsLoading, hasMoreGroups]);

  useEffect(() => {
    setMessagesPage(1);
  }, [selectedGroupId]);

  const filteredGroups = allGroups.filter((group) =>
    group.name?.toLowerCase().includes(groupSearch.toLowerCase())
  );

  const selectedGroup = allGroups.find(
    (group) => group.group_id === selectedGroupId
  );

  const selectGroup = (groupId: string) => {
    setSelectedGroupId(groupId);
    setSearchParams({ group_id: groupId }, { replace: true });
  };

  const loadMoreGroups = useCallback(() => {
    if (!groupsLoading && hasMoreGroups) {
      setGroupsPage((page) => page + 1);
    }
  }, [groupsLoading, hasMoreGroups]);

  const handleGroupsScroll = () => {
    const container = groupsListRef.current;
    if (!container) {
      return;
    }

    const nearBottom =
      container.scrollTop + container.clientHeight >= container.scrollHeight - 48;
    if (nearBottom) {
      loadMoreGroups();
    }
  };

  const handleSendMessage = () => {
    if (messageText && selectedGroupId) {
      sendMessage.mutate(
        { groupId: selectedGroupId, message: messageText },
        { onSuccess: () => setMessageText("") }
      );
    }
  };

  if (groupsLoading && allGroups.length === 0) {
    return <LoadingState />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Messenger"
        description={`${groupsPageData?.total_groups ?? allGroups.length} groups`}
      />

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle>Groups</CardTitle>
            <Input
              placeholder="Search groups..."
              value={groupSearch}
              onChange={(e) => setGroupSearch(e.target.value)}
              className="mt-2"
            />
          </CardHeader>
          <CardContent>
            <div
              ref={groupsListRef}
              onScroll={handleGroupsScroll}
              className="space-y-1 max-h-96 overflow-auto"
            >
              {filteredGroups.map((group) => (
                <div
                  key={group.group_id}
                  onClick={() => selectGroup(group.group_id)}
                  className={`cursor-pointer rounded-md p-2 text-sm transition-colors ${
                    selectedGroupId === group.group_id
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-muted"
                  }`}
                >
                  {group.name}
                </div>
              ))}
              {groupsLoading && (
                <p className="p-2 text-xs text-muted-foreground">Loading groups...</p>
              )}
              {!groupsLoading && hasMoreGroups && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full"
                  onClick={loadMoreGroups}
                >
                  Load more groups
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>
              {selectedGroup?.name ?? "Select a group"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {selectedGroupId ? (
              <div className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="Type a message..."
                    value={messageText}
                    onChange={(e) => setMessageText(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
                  />
                  <Button onClick={handleSendMessage} disabled={sendMessage.isPending}>
                    Send
                  </Button>
                </div>

                <div className="border rounded-md">
                  <div className="bg-muted p-2 text-sm font-medium">
                    Recent Messages
                  </div>
                  <div className="max-h-64 overflow-auto p-2 space-y-2">
                    {messagesLoading && messagesPage === 1 ? (
                      <p className="text-sm text-muted-foreground">Loading messages...</p>
                    ) : messages?.messages?.length ? (
                      messages.messages.map((msg) => (
                        <div
                          key={msg.message_id}
                          className="rounded-md border p-2 text-sm"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-medium">
                              {msg.from_bakchod.pretty_name ??
                                msg.from_bakchod.username ??
                                "Unknown"}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {formatDate(msg.time_sent)}
                            </span>
                          </div>
                          <p className="mt-1">{msg.text || "<no text>"}</p>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-muted-foreground">
                        No messages yet
                      </p>
                    )}
                  </div>
                  {messages && messages.total_pages > 1 && (
                    <div className="flex items-center justify-center gap-2 border-t p-2">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={messagesPage === 1}
                        onClick={() => setMessagesPage((page) => page - 1)}
                      >
                        Previous
                      </Button>
                      <span className="text-xs text-muted-foreground">
                        Page {messages.current_page} of {messages.total_pages}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={messagesPage >= messages.total_pages}
                        onClick={() => setMessagesPage((page) => page + 1)}
                      >
                        Next
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-muted-foreground">
                Select a group from the list to send a message
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
