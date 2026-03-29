"use client";

import { useId } from "react";
import { Area, AreaChart, Tooltip, XAxis, YAxis } from "recharts";
import type { TrendPoint } from "@/lib/types";

interface InlineChartProps {
  data: TrendPoint[];
  color?: string;
}

export function InlineChart({ data, color = "#d9574f" }: InlineChartProps) {
  const gradientId = useId().replace(/:/g, "");

  return (
    <div className="h-44 w-full min-w-0">
      <AreaChart
        responsive
        data={data}
        style={{ width: "100%", height: "100%" }}
        margin={{ top: 12, right: 4, left: -28, bottom: 0 }}
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.3} />
            <stop offset="100%" stopColor={color} stopOpacity={0.04} />
          </linearGradient>
        </defs>
        <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fill: "#7f90a3", fontSize: 11 }} />
        <YAxis tickLine={false} axisLine={false} tick={{ fill: "#7f90a3", fontSize: 11 }} />
        <Tooltip
          cursor={{ stroke: "rgba(217,87,79,0.2)" }}
          contentStyle={{ backgroundColor: "#111821", border: "1px solid rgba(137,155,176,0.18)", borderRadius: "8px" }}
          labelStyle={{ color: "#eef3f8" }}
        />
        <Area type="monotone" dataKey="score" stroke={color} strokeWidth={2} fill={`url(#${gradientId})`} />
      </AreaChart>
    </div>
  );
}
