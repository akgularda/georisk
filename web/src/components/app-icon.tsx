import type { ReactNode, SVGProps } from "react";

export type AppIconName =
  | "security"
  | "insights"
  | "public"
  | "table_chart"
  | "folder_open"
  | "notifications"
  | "account_circle"
  | "location_on"
  | "arrow_forward"
  | "filter_list"
  | "grid_view";

interface AppIconProps extends SVGProps<SVGSVGElement> {
  name: AppIconName;
}

const iconPaths: Record<AppIconName, ReactNode> = {
  security: (
    <>
      <path d="M12 3l7 3v5c0 4.6-2.9 8.9-7 10-4.1-1.1-7-5.4-7-10V6l7-3Z" />
      <path d="M9.5 12.5l1.7 1.7 3.3-3.9" />
    </>
  ),
  insights: (
    <>
      <path d="M5 17 10 12l3 3 6-7" />
      <path d="M5 7h3v10H5z" />
      <path d="M10.5 9H13v8h-2.5z" />
      <path d="M15.5 5H18v12h-2.5z" />
    </>
  ),
  public: (
    <>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M3.5 12h17" />
      <path d="M12 3.5c2.3 2.2 3.5 5.2 3.5 8.5s-1.2 6.3-3.5 8.5c-2.3-2.2-3.5-5.2-3.5-8.5s1.2-6.3 3.5-8.5Z" />
    </>
  ),
  table_chart: (
    <>
      <rect x="4" y="5" width="16" height="14" rx="1.5" />
      <path d="M4 10h16M9 5v14M15 5v14" />
    </>
  ),
  folder_open: (
    <>
      <path d="M4 8.5A1.5 1.5 0 0 1 5.5 7H10l2 2h6.5A1.5 1.5 0 0 1 20 10.5v6A1.5 1.5 0 0 1 18.5 18h-13A1.5 1.5 0 0 1 4 16.5v-8Z" />
      <path d="M4 10h16l-1.5 6.5A1.5 1.5 0 0 1 17 18H5.5A1.5 1.5 0 0 1 4 16.5V10Z" />
    </>
  ),
  notifications: (
    <>
      <path d="M12 4.5a4 4 0 0 1 4 4v1.3c0 1 .3 2 .9 2.8l1.1 1.4H6l1.1-1.4c.6-.8.9-1.8.9-2.8V8.5a4 4 0 0 1 4-4Z" />
      <path d="M10 17a2 2 0 0 0 4 0" />
    </>
  ),
  account_circle: (
    <>
      <circle cx="12" cy="12" r="8.5" />
      <circle cx="12" cy="9" r="2.5" />
      <path d="M7.5 17c1.2-1.8 2.8-2.7 4.5-2.7s3.3.9 4.5 2.7" />
    </>
  ),
  location_on: (
    <>
      <path d="M12 20s5-4.6 5-9a5 5 0 1 0-10 0c0 4.4 5 9 5 9Z" />
      <circle cx="12" cy="11" r="1.75" />
    </>
  ),
  arrow_forward: (
    <>
      <path d="M5 12h12" />
      <path d="m13 7 5 5-5 5" />
    </>
  ),
  filter_list: (
    <>
      <path d="M4 7h16" />
      <path d="M7 12h10" />
      <path d="M10 17h4" />
    </>
  ),
  grid_view: (
    <>
      <rect x="4" y="4" width="6.5" height="6.5" rx="1" />
      <rect x="13.5" y="4" width="6.5" height="6.5" rx="1" />
      <rect x="4" y="13.5" width="6.5" height="6.5" rx="1" />
      <rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1" />
    </>
  ),
};

export function AppIcon({ name, className, ...props }: AppIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
      {...props}
    >
      {iconPaths[name]}
    </svg>
  );
}
