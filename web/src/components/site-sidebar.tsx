import { AppIcon } from "@/components/app-icon";
import Link from "next/link";
import { SiteNavLinks } from "@/components/site-nav-links";

export function SiteSidebar() {
  return (
    <aside className="shell-sidebar fixed left-0 top-16 hidden h-[calc(100vh-4rem)] w-64 flex-col p-4 lg:flex">
      <div className="mb-8 px-2">
        <div className="mb-1 flex items-center space-x-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-sm border border-[rgba(69,70,77,0.2)] bg-surface-high">
            <AppIcon name="security" className="h-4 w-4 text-primary" />
          </div>
          <div>
            <div className="font-headline text-sm font-bold uppercase tracking-tight text-foreground">Command Center</div>
            <div className="text-[10px] font-medium uppercase tracking-[0.24em] text-[rgba(218,226,253,0.55)]">Level 4 Clearance</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1">
        <SiteNavLinks variant="sidebar" />
      </nav>

      <Link
        href="/reports"
        className="mt-auto inline-flex w-full items-center justify-center bg-gradient-to-r from-primary to-primary-strong px-4 py-3 text-[11px] font-bold uppercase tracking-[0.22em] text-[#2a1700] transition-all hover:shadow-[0_0_20px_rgba(244,47,84,0.3)]"
      >
        Generate Report
      </Link>
    </aside>
  );
}
