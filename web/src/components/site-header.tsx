import { AppIcon } from "@/components/app-icon";
import { SiteNavLinks } from "@/components/site-nav-links";
import { siteConfig } from "@/lib/site";

export function SiteHeader() {
  return (
    <header className="shell-topbar fixed inset-x-0 top-0 z-50 h-16">
      <div className="flex h-full items-center justify-between px-6">
        <div className="font-headline text-2xl font-bold tracking-[-0.06em] text-foreground">{siteConfig.shortName}</div>

        <nav className="hidden h-full items-center space-x-8 md:flex">
          <SiteNavLinks variant="header" />
        </nav>

        <div className="flex items-center space-x-4">
          <button className="rounded-sm p-2 transition-all duration-200 hover:bg-surface-high" aria-label="Notifications">
            <AppIcon name="notifications" className="h-5 w-5 text-[rgba(218,226,253,0.6)]" />
          </button>
          <button className="rounded-sm p-2 transition-all duration-200 hover:bg-surface-high" aria-label="Profile">
            <AppIcon name="account_circle" className="h-5 w-5 text-[rgba(218,226,253,0.6)]" />
          </button>
        </div>
      </div>
    </header>
  );
}
