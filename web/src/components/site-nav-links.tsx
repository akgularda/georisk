"use client";

import { AppIcon, type AppIconName } from "@/components/app-icon";
import Link from "next/link";
import { usePathname } from "next/navigation";

type SiteNavVariant = "header" | "sidebar" | "mobile";

interface HeaderNavItem {
  href: string;
  label: string;
}

interface ShellNavItem extends HeaderNavItem {
  icon: AppIconName;
}

const headerItems: HeaderNavItem[] = [
  { href: "/", label: "Dashboard" },
  { href: "/reports", label: "Reports" },
  { href: "/status", label: "Settings" },
];

const shellItems: ShellNavItem[] = [
  { href: "/", label: "Intelligence", icon: "insights" },
  { href: "/forecasts", label: "Global Map", icon: "public" },
  { href: "/countries", label: "Risk Matrix", icon: "table_chart" },
  { href: "/reports", label: "Archives", icon: "folder_open" },
];

interface SiteNavLinksProps {
  variant: SiteNavVariant;
}

export function SiteNavLinks({ variant }: SiteNavLinksProps) {
  const pathname = usePathname();

  if (variant === "header") {
    return (
      <>
        {headerItems.map((item) => {
          const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

          return (
            <Link key={item.href} href={item.href} className={`command-top-link ${active ? "command-top-link-active" : ""}`}>
              {item.label}
            </Link>
          );
        })}
      </>
    );
  }

  return (
    <>
      {shellItems.map((item) => {
        const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

        if (variant === "mobile") {
          return (
            <Link key={item.href} href={item.href} className={`command-mobile-link ${active ? "command-mobile-link-active" : ""}`}>
              <AppIcon name={item.icon} className="h-5 w-5" />
              <span className="text-[10px] font-medium uppercase tracking-[0.18em]">{item.label}</span>
            </Link>
          );
        }

        return (
          <Link key={item.href} href={item.href} className={`command-sidebar-link ${active ? "command-sidebar-link-active" : ""}`}>
            <AppIcon name={item.icon} className="h-5 w-5" />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </>
  );
}
