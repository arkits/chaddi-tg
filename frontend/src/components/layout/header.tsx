import { Link, useLocation } from "react-router-dom";
import { navItems } from "./sidebar";

export default function Header() {
  const location = useLocation();

  return (
    <header className="sticky top-0 z-30 border-b border-border/55 bg-background/55 px-4 py-3 backdrop-blur-xl sm:px-6">
      <div className="mb-2 flex items-center justify-between lg:mb-0">
        <div className="lg:hidden">
          <p className="text-[10px] uppercase tracking-[0.2em] text-primary/90">Chaddi TG</p>
          <p className="text-sm text-muted-foreground">Control panel</p>
        </div>
      </div>

      <nav className="scrollbar-theme flex gap-2 overflow-auto pb-1 lg:hidden">
        {navItems.map((item) => {
          const active =
            item.to === "/"
              ? location.pathname === item.to
              : location.pathname.startsWith(item.to);
          return (
            <Link
              key={item.to}
              to={item.to}
              viewTransition
              className={
                active
                  ? "rounded-full border border-primary/50 bg-primary/20 px-3 py-1.5 text-xs font-semibold text-foreground"
                  : "rounded-full border border-border/70 bg-background/50 px-3 py-1.5 text-xs font-medium text-muted-foreground"
              }
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}
