import type { ElementType } from "react";
import {
  Users,
  MessageSquare,
  Quote,
  Clock,
  Activity,
  GitCommitHorizontal,
  Timer,
} from "lucide-react";
import { LoadingState } from "@/components/shared/loading-state";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useDashboardMetrics,
  useDashboardActivity,
  useDashboardRandomQuote,
  useDashboardVersion,
} from "@/hooks/use-dashboard";
import { formatNumber, formatRelativeTime } from "@/lib/utils";

interface StatTile {
  title: string;
  value: number;
  icon: ElementType;
  cardClass: string;
}

export default function Dashboard() {
  const { data: metrics, isLoading: metricsLoading } = useDashboardMetrics();
  const { data: activity } = useDashboardActivity();
  const { data: randomQuote } = useDashboardRandomQuote();
  const { data: version } = useDashboardVersion();

  if (metricsLoading) {
    return <LoadingState />;
  }

  const stats: StatTile[] = [
    {
      title: "Total Bakchods",
      value: metrics?.bakchods_count ?? 0,
      icon: Users,
      cardClass:
        "border-amber-200/30 !bg-gradient-to-br !from-amber-500/14 !via-card !to-card",
    },
    {
      title: "Total Groups",
      value: metrics?.groups_count ?? 0,
      icon: MessageSquare,
      cardClass:
        "border-emerald-200/30 !bg-gradient-to-br !from-emerald-500/14 !via-card !to-card",
    },
    {
      title: "Total Quotes",
      value: metrics?.quotes_count ?? 0,
      icon: Quote,
      cardClass:
        "border-rose-200/30 !bg-gradient-to-br !from-rose-500/14 !via-card !to-card",
    },
    {
      title: "Active Jobs",
      value: metrics?.jobs_count ?? 0,
      icon: Clock,
      cardClass:
        "border-sky-200/30 !bg-gradient-to-br !from-sky-500/14 !via-card !to-card",
    },
  ];

  const totalMessages = metrics?.messages_count ?? 0;
  const recentMessages = metrics?.recent_messages ?? 0;
  const totalBakchods = metrics?.bakchods_count ?? 0;
  const recentBakchods = metrics?.recent_bakchods ?? 0;
  const messages24hShare = totalMessages > 0 ? (recentMessages / totalMessages) * 100 : 0;
  const activeUsers24hShare =
    totalBakchods > 0 ? (recentBakchods / totalBakchods) * 100 : 0;
  const avgMessagesPerGroup =
    (metrics?.groups_count ?? 0) > 0
      ? totalMessages / (metrics?.groups_count ?? 1)
      : 0;

  return (
    <div className="space-y-8">
      <section className="relative overflow-hidden rounded-3xl border border-border/60 bg-card/65 p-6 backdrop-blur lg:p-8">
        <div className="pointer-events-none absolute -right-10 -top-16 h-52 w-52 rounded-full bg-gradient-to-br from-orange-400/25 to-transparent blur-2xl" />
        <div className="pointer-events-none absolute -left-10 bottom-0 h-44 w-44 rounded-full bg-gradient-to-br from-cyan-400/20 to-transparent blur-2xl" />

        <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-4">
            <div>
              <h1 className="text-3xl font-semibold tracking-tight lg:text-4xl">
                Chaddi TG Dashboard
              </h1>
              <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
                Live snapshot of users, groups, quotes, and bot runtime health.
              </p>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl border border-border/70 bg-background/50 px-4 py-3">
              <p className="text-xs text-muted-foreground">Latest Message</p>
              <p className="mt-1 text-sm font-semibold">
                {activity?.latest_message_time
                  ? formatRelativeTime(activity.latest_message_time)
                  : "No activity"}
              </p>
            </div>
            <div className="rounded-xl border border-border/70 bg-background/50 px-4 py-3">
              <p className="text-xs text-muted-foreground">Version</p>
              <p className="mt-1 font-mono text-sm font-semibold">
                {version?.semver ?? "unknown"}
              </p>
            </div>
            <div className="rounded-xl border border-border/70 bg-background/50 px-4 py-3">
              <p className="text-xs text-muted-foreground">Uptime</p>
              <p className="mt-1 font-mono text-sm font-semibold">
                {version?.pretty_uptime ?? "unknown"}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card
              key={stat.title}
              className={`overflow-hidden ${stat.cardClass}`}
            >
              <CardHeader className="flex flex-row items-start justify-between pb-2">
                <div>
                  <p className="text-xs uppercase tracking-widest text-muted-foreground">
                    {stat.title}
                  </p>
                  <CardTitle className="mt-3 text-3xl">
                    {formatNumber(stat.value)}
                  </CardTitle>
                </div>
                <div className="rounded-lg border border-border/70 bg-background/70 p-2">
                  <Icon className="h-4 w-4 text-foreground/85" />
                </div>
              </CardHeader>
            </Card>
          );
        })}
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl">
              <Activity className="h-5 w-5 text-cyan-300" />
              Activity Pulse
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Messages in last 24h</span>
                <span className="font-semibold">{formatNumber(recentMessages)}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 transition-all"
                  style={{ width: `${Math.min(messages24hShare, 100)}%` }}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                {messages24hShare.toFixed(1)}% of total message volume
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Active users in last 24h</span>
                <span className="font-semibold">{formatNumber(recentBakchods)}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-teal-500 transition-all"
                  style={{ width: `${Math.min(activeUsers24hShare, 100)}%` }}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                {activeUsers24hShare.toFixed(1)}% of tracked users
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl border border-border/70 bg-background/60 p-4">
                <p className="text-xs text-muted-foreground">Total Messages</p>
                <p className="mt-1 text-xl font-semibold">
                  {formatNumber(totalMessages)}
                </p>
              </div>
              <div className="rounded-xl border border-border/70 bg-background/60 p-4">
                <p className="text-xs text-muted-foreground">Roll Events</p>
                <p className="mt-1 text-xl font-semibold">
                  {formatNumber(metrics?.roll_count ?? 0)}
                </p>
              </div>
              <div className="rounded-xl border border-border/70 bg-background/60 p-4">
                <p className="text-xs text-muted-foreground">Msgs per Group</p>
                <p className="mt-1 text-xl font-semibold">
                  {avgMessagesPerGroup > 0 ? avgMessagesPerGroup.toFixed(1) : "0.0"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="overflow-hidden border-rose-300/20 bg-gradient-to-br from-rose-500/10 via-card to-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl">
              <Quote className="h-5 w-5 text-rose-300" />
              Quote Spotlight
            </CardTitle>
          </CardHeader>
          <CardContent>
            {randomQuote?.quote ? (
              <div className="space-y-4">
                <p className="text-base italic leading-relaxed text-foreground/90">
                  "{randomQuote.quote.text}"
                </p>
                <div className="h-px w-full bg-border/80" />
                <p className="text-sm text-muted-foreground">
                  {randomQuote.quote.author_bakchod.pretty_name ||
                    randomQuote.quote.author_bakchod.username}
                  {" in "}
                  {randomQuote.quote.quoted_in_group.name}
                </p>
              </div>
            ) : (
              <p className="text-muted-foreground">No quotes available yet.</p>
            )}
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-xl">Leaderboard</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between rounded-xl border border-border/60 bg-background/50 p-4">
              <span className="text-sm text-muted-foreground">Most Active User</span>
              <span className="font-semibold">
                {activity?.most_active_bakchod
                  ? activity.most_active_bakchod.pretty_name ??
                    activity.most_active_bakchod.username ??
                    "Unknown"
                  : "Unknown"}
              </span>
            </div>
            <div className="flex items-center justify-between rounded-xl border border-border/60 bg-background/50 p-4">
              <span className="text-sm text-muted-foreground">Most Active Group</span>
              <span className="font-semibold">
                {activity?.most_active_group?.name || "Unknown"}
              </span>
            </div>
            <div className="flex items-center justify-between rounded-xl border border-border/60 bg-background/50 p-4">
              <span className="text-sm text-muted-foreground">Last Message Seen</span>
              <span className="font-semibold">
                {activity?.latest_message_time
                  ? formatRelativeTime(activity.latest_message_time)
                  : "No messages"}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl">
              <GitCommitHorizontal className="h-5 w-5 text-orange-300" />
              Build Snapshot
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm">
            <div className="flex items-center justify-between rounded-xl border border-border/60 bg-background/50 p-4">
              <span className="text-muted-foreground">Version</span>
              <span className="font-mono">{version?.semver ?? "unknown"}</span>
            </div>
            <div className="flex items-center justify-between rounded-xl border border-border/60 bg-background/50 p-4">
              <span className="text-muted-foreground">Git Commit</span>
              <span className="max-w-[12rem] truncate font-mono">
                {version?.git_commit_id ?? "unknown"}
              </span>
            </div>
            <div className="flex items-center justify-between rounded-xl border border-border/60 bg-background/50 p-4">
              <span className="text-muted-foreground">Commit Time</span>
              <span className="font-mono text-xs">
                {version?.git_commit_time ?? "unknown"}
              </span>
            </div>
            <div className="flex items-center justify-between rounded-xl border border-border/60 bg-background/50 p-4">
              <span className="flex items-center gap-2 text-muted-foreground">
                <Timer className="h-4 w-4" />
                Uptime
              </span>
              <span className="font-mono">{version?.pretty_uptime ?? "unknown"}</span>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
