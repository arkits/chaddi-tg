import { useParams, useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { MetadataEditor } from "@/components/shared/metadata-editor";
import { GroupCommandSettings } from "@/components/shared/group-command-settings";
import { DataTable } from "@/components/shared/data-table";
import {
  useGroup,
  useGroupMembers,
  useGroupMessages,
  useSendMessageToGroup,
  useSetGroupMetadata,
  type GroupMember,
} from "@/hooks/use-groups";
import { formatDate, formatNumber } from "@/lib/utils";
import { useState } from "react";
import { ArrowLeft, Send } from "lucide-react";

export default function GroupDetail() {
  const { groupId } = useParams<{ groupId: string }>();
  const navigate = useNavigate();
  const { data: group, isLoading } = useGroup(groupId!);
  const { data: members } = useGroupMembers(groupId!);
  const [messagesPage, setMessagesPage] = useState(1);
  const [includeUpdate, setIncludeUpdate] = useState(false);
  const { data: messages } = useGroupMessages(groupId!, messagesPage, includeUpdate);
  const sendMessage = useSendMessageToGroup();
  const setMetadata = useSetGroupMetadata();

  const [messageText, setMessageText] = useState("");

  if (isLoading) {
    return <LoadingState />;
  }

  if (!group) {
    return (
      <div className="space-y-6">
        <Button
          variant="ghost"
          onClick={() => navigate("/groups", { viewTransition: true })}
        >
          <ArrowLeft className="mr-2 h-4 w-4" /> Back
        </Button>
        <p>Group not found</p>
      </div>
    );
  }

  const groupMetadata = group.metadata ?? {};

  const handleSendMessage = () => {
    if (messageText && groupId) {
      sendMessage.mutate(
        { groupId, message: messageText },
        { onSuccess: () => setMessageText("") }
      );
    }
  };

  const memberColumns = [
    {
      key: "tg_id",
      header: "ID",
      render: (member: GroupMember) => (
        <span className="font-mono text-xs">{member.tg_id}</span>
      ),
    },
    {
      key: "username",
      header: "Username",
      render: (member: GroupMember) => member.username ?? "-",
    },
    {
      key: "pretty_name",
      header: "Name",
      render: (member: GroupMember) => member.pretty_name ?? "-",
    },
    {
      key: "rokda",
      header: "Rokda",
      render: (member: GroupMember) => formatNumber(Math.floor(member.rokda)),
    },
    {
      key: "lastseen",
      header: "Last Seen",
      render: (member: GroupMember) =>
        member.lastseen ? formatDate(member.lastseen) : "Never",
    },
    {
      key: "actions",
      header: "",
      render: (member: GroupMember) => (
        <Button
          variant="outline"
          size="sm"
          onClick={() =>
            navigate(`/bakchods/${member.tg_id}`, { viewTransition: true })
          }
        >
          View
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title={group.name ?? "Unknown"} description={`ID: ${group.group_id}`}>
        <Button
          variant="ghost"
          onClick={() => navigate("/groups", { viewTransition: true })}
        >
          <ArrowLeft className="mr-2 h-4 w-4" /> Back
        </Button>
      </PageHeader>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Group Info</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Group ID</span>
              <span className="font-mono text-xs">{group.group_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Created</span>
              <span>{group.created ? formatDate(group.created) : "-"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Updated</span>
              <span>{group.updated ? formatDate(group.updated) : "-"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Members</span>
              <span>{members?.total ?? 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Messages</span>
              <span>{messages?.total_messages ?? 0}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Send Message</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                placeholder="Message text"
                value={messageText}
                onChange={(e) => setMessageText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
              />
              <Button onClick={handleSendMessage} disabled={sendMessage.isPending}>
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <GroupCommandSettings groupId={group.group_id} metadata={groupMetadata} />

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-4">
          <CardTitle>Members ({members?.total ?? 0})</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={memberColumns}
            data={members?.members ?? []}
            keyExtractor={(member) => member.tg_id}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle>Messages ({messages?.total_messages ?? 0})</CardTitle>
          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <input
              type="checkbox"
              checked={includeUpdate}
              onChange={(e) => {
                setIncludeUpdate(e.target.checked);
                setMessagesPage(1);
              }}
              className="rounded border-input"
            />
            Show raw update JSON
          </label>
        </CardHeader>
        <CardContent className="space-y-4">
          {messages && messages.messages.length > 0 ? (
            <div className="space-y-2 max-h-96 overflow-auto">
              {messages.messages.map((msg) => (
                <div
                  key={msg.message_id}
                  className="rounded-md border p-3 space-y-1"
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
                  <p className="text-sm">{msg.text || "<no text>"}</p>
                  {includeUpdate && msg.update && (
                    <pre className="overflow-auto rounded-md bg-muted p-2 text-xs">
                      {msg.update}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">No messages found</p>
          )}

          {messages && messages.total_pages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={messagesPage === 1}
                onClick={() => setMessagesPage((page) => page - 1)}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
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
        </CardContent>
      </Card>

      <MetadataEditor
        metadata={groupMetadata}
        isPending={setMetadata.isPending}
        onSave={(metadataJson) => {
          setMetadata.mutate({ groupId: group.group_id, metadata: metadataJson });
        }}
      />
    </div>
  );
}
