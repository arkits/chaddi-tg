import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  MessageSquare,
  Quote,
  Clock,
  Terminal,
  FileText,
  Send,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useDashboardVersion } from "@/hooks/use-dashboard";

export const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/bakchods", label: "Bakchods", icon: Users },
  { to: "/groups", label: "Groups", icon: MessageSquare },
  { to: "/quotes", label: "Quotes", icon: Quote },
  { to: "/jobs", label: "Jobs", icon: Clock },
  { to: "/commands", label: "Commands", icon: Terminal },
  { to: "/logs", label: "Logs", icon: FileText },
  { to: "/messenger", label: "Messenger", icon: Send },
];

type SidebarProps = {
  collapsed: boolean;
  onToggle: () => void;
};

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const { data: version } = useDashboardVersion();

  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-40 hidden p-4 transition-[width] duration-200 lg:block",
        collapsed ? "w-24" : "w-72"
      )}
    >
      <div className="flex h-full flex-col">
        <div className="surface-panel flex h-full flex-col rounded-3xl p-4">
          <div
            className={cn(
              "mb-6 border border-border/70 bg-background/55 p-4",
              collapsed ? "flex items-center justify-center" : "space-y-2"
            )}
          >
            {collapsed ? (
              <h1 className="text-lg font-semibold leading-none">CT</h1>
            ) : (
              <>
                <p className="text-[11px] uppercase tracking-[0.2em] text-primary/90">
                  Control Plane
                </p>
                <h1 className="text-2xl font-semibold leading-none">Chaddi TG</h1>
                <p className="text-sm text-muted-foreground">
                  Telegram operations dashboard
                </p>
              </>
            )}
          </div>

          <button
            type="button"
            onClick={onToggle}
            className="mb-3 flex items-center justify-center border border-border bg-background/40 px-2 py-2 text-muted-foreground transition-colors hover:text-foreground"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? (
              <PanelLeftOpen className="h-4 w-4" />
            ) : (
              <PanelLeftClose className="h-4 w-4" />
            )}
          </button>

          <nav className="space-y-1.5">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                viewTransition
                title={item.label}
                className={({ isActive }) =>
                  cn(
                    "group flex items-center px-3 py-2.5 text-sm font-medium transition-all duration-200",
                    collapsed ? "justify-center" : "gap-3",
                    isActive
                      ? "border border-primary/45 bg-primary/20 text-foreground shadow-[0_8px_28px_hsl(var(--primary)/0.22)]"
                      : "text-muted-foreground hover:bg-background/55 hover:text-foreground"
                  )
                }
              >
                <span className="rounded-lg border border-border/70 bg-background/50 p-1.5 group-hover:border-primary/50">
                  <item.icon className="h-3.5 w-3.5" />
                </span>
                {!collapsed && item.label}
              </NavLink>
            ))}
          </nav>

          <div
            className={cn(
              "mt-auto border-2 border-border p-3 text-xs text-muted-foreground",
              collapsed && "text-center"
            )}
          >
            {version ? (
              <div className={cn("space-y-1", collapsed && "space-y-2")}>
                <p className="font-mono text-[11px] text-foreground">v{version.semver}</p>
                {!collapsed && <p className="font-mono text-[11px]">{version.pretty_uptime}</p>}
              </div>
            ) : (
              <p className="font-mono text-[11px]">Version unavailable</p>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}
