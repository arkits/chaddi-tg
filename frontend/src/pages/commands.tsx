import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { MetricCard } from "@/components/shared/metric-card";
import {
  useCommandStats,
  useTopCommands,
  useCommandsByGroup,
  useCommandsByUser,
  useCommandsHourly,
  useCommandsRecent,
} from "@/hooks/use-commands";
import { Terminal, TrendingUp, Users, MessageSquare } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
} from "recharts";
import { formatDate, formatNumber } from "@/lib/utils";

export default function Commands() {
  const { data: stats, isLoading: statsLoading } = useCommandStats();
  const { data: topCommands } = useTopCommands();
  const { data: byGroup } = useCommandsByGroup();
  const { data: byUser } = useCommandsByUser();
  const { data: hourly } = useCommandsHourly();
  const { data: recent } = useCommandsRecent();

  if (statsLoading) {
    return <LoadingState />;
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Commands" description="Command usage analytics" />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Total Commands"
          value={stats?.total ?? 0}
          icon={<Terminal className="h-4 w-4 text-muted-foreground" />}
          isLoading={statsLoading}
        />
        <MetricCard
          title="Last 24 Hours"
          value={stats?.last_24h ?? 0}
          icon={<TrendingUp className="h-4 w-4 text-muted-foreground" />}
          isLoading={statsLoading}
        />
        <MetricCard
          title="Last 7 Days"
          value={stats?.last_7d ?? 0}
          icon={<TrendingUp className="h-4 w-4 text-muted-foreground" />}
          isLoading={statsLoading}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Top Commands</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topCommands?.slice(0, 8) ?? []}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    dataKey="command_name"
                    className="text-xs"
                    tick={{ fill: "hsl(var(--muted-foreground))" }}
                  />
                  <YAxis
                    className="text-xs"
                    tick={{ fill: "hsl(var(--muted-foreground))" }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "var(--radius)",
                    }}
                  />
                  <Bar dataKey="count" fill="hsl(var(--primary))" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Hourly Distribution (24h)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={hourly ?? []}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    dataKey="hour"
                    className="text-xs"
                    tick={{ fill: "hsl(var(--muted-foreground))" }}
                  />
                  <YAxis
                    className="text-xs"
                    tick={{ fill: "hsl(var(--muted-foreground))" }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "var(--radius)",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke="hsl(var(--primary))"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Top Groups
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {byGroup?.map((g, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-md border p-2"
                >
                  <span className="text-sm">{g.name}</span>
                  <span className="font-mono text-sm">{formatNumber(g.count)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Top Users
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {byUser?.map((u, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-md border p-2"
                >
                  <span className="text-sm">{u.pretty_name ?? u.username}</span>
                  <span className="font-mono text-sm">{formatNumber(u.count)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Commands</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 max-h-96 overflow-auto">
            {recent?.map((cmd) => (
              <div
                key={cmd.id}
                className="flex items-center justify-between rounded-md border p-2"
              >
                <div className="flex items-center gap-2">
                  <code className="text-sm bg-muted px-2 py-0.5 rounded">
                    /{cmd.command_name}
                  </code>
                  <span className="text-sm text-muted-foreground">
                    by {cmd.from_bakchod ?? "Unknown"}
                  </span>
                  {cmd.group && (
                    <span className="text-xs text-muted-foreground">
                      in {cmd.group}
                    </span>
                  )}
                </div>
                <span className="text-xs text-muted-foreground">
                  {formatDate(cmd.executed_at)}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}