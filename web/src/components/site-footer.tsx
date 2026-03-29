import { SiteNavLinks } from "@/components/site-nav-links";

export function SiteFooter() {
  return (
    <nav className="fixed inset-x-0 bottom-0 z-50 flex h-16 items-center justify-around border-t border-[rgba(69,70,77,0.16)] bg-background md:hidden">
      <SiteNavLinks variant="mobile" />
    </nav>
  );
}
