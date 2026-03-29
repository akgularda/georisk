import clsx from "clsx";
import { countryShapes } from "@/lib/country-shapes";
import type { CountryShapeKey } from "@/lib/types";

interface CountryPulseGraphicProps {
  country: CountryShapeKey | null;
  title: string;
  label?: string;
  iso3?: string;
  framed?: boolean;
  size?: "theater" | "dossier";
  className?: string;
}

const shapeScaleByCountry: Record<CountryShapeKey, number> = {
  iran: 1.02,
  israel: 1.1,
  sudan: 1.02,
  ukraine: 1.05,
  syria: 1.03,
  colombia: 1.03,
  taiwan: 1.05,
  lebanon: 1.07,
};

export function CountryPulseGraphic({
  country,
  title,
  label,
  iso3,
  framed = true,
  size = "dossier",
  className,
}: CountryPulseGraphicProps) {
  const frameClasses = framed ? "rounded-lg border border-[rgba(255,96,74,0.4)] shadow-[0_18px_44px_rgba(0,0,0,0.42)]" : "";
  const heightClasses = size === "theater" ? "min-h-[320px] md:min-h-[380px]" : "min-h-[300px] md:min-h-[340px]";
  const svgClasses = size === "theater" ? "h-[248px] w-[248px] md:h-[312px] md:w-[312px]" : "h-[216px] w-[216px] md:h-[272px] md:w-[272px]";
  const theaterMode = size === "theater";
  const plateInset = theaterMode ? "inset-[10px] md:inset-[12px]" : "inset-[12px]";
  const shapePath = country ? countryShapes[country] : null;
  const shapeScale = country ? shapeScaleByCountry[country] ?? 1 : 1;
  const shapeTransform = `translate(180 180) scale(${shapeScale}) translate(-180 -180)`;
  const strokeWidth = theaterMode ? 2.6 : 2.25;

  return (
    <div className={clsx("relative isolate overflow-hidden bg-[#15090a] text-[#fff2ee]", heightClasses, frameClasses, className)}>
      <div className="alert-plate absolute inset-0" />
      <div className={clsx("alert-plate-grid absolute", plateInset, theaterMode ? "opacity-60" : "opacity-45")} />
      <div className={clsx("alert-plate-wash absolute", plateInset, theaterMode ? "opacity-100" : "opacity-80")} />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[2px]" style={{ background: "rgba(255, 88, 76, 0.84)" }} />
      <div className={clsx("pointer-events-none absolute", plateInset)} style={{ border: "1px solid rgba(255,118,99,0.46)" }} />
      <div className="absolute left-4 top-4 z-20">
        <div className="text-[0.54rem] font-black uppercase tracking-[0.34em] text-[#ffe1da]">Emergency Feed</div>
        <div className="mt-1 text-[0.52rem] font-semibold uppercase tracking-[0.3em] text-[rgba(255,210,201,0.72)]">Country Outline</div>
      </div>
      <div className="relative z-10 flex h-full items-center justify-center px-5 py-6 md:px-6">
        <div
          className="pointer-events-none absolute inset-x-[12%] top-1/2 h-[34%] -translate-y-1/2"
          style={{
            background:
              "linear-gradient(90deg, rgba(255,102,82,0) 0%, rgba(255,102,82,0.06) 14%, rgba(255,102,82,0.14) 50%, rgba(255,102,82,0.06) 86%, rgba(255,102,82,0) 100%)",
          }}
        />
        {shapePath ? (
          <svg viewBox="0 0 360 360" className={svgClasses} role="img" aria-label={`${title} silhouette`}>
            <g transform={shapeTransform}>
              <path
                d={shapePath}
                fill="rgba(255, 88, 76, 0.12)"
                stroke="none"
                fillRule="evenodd"
                vectorEffect="non-scaling-stroke"
              />
              <path
                d={shapePath}
                fill="rgba(128, 18, 14, 0.96)"
                stroke="rgba(255, 108, 92, 0.98)"
                strokeWidth={strokeWidth}
                fillRule="evenodd"
                vectorEffect="non-scaling-stroke"
              />
              <path
                d={shapePath}
                fill="none"
                stroke="rgba(255, 224, 218, 0.16)"
                strokeWidth={theaterMode ? 0.95 : 0.82}
                fillRule="evenodd"
                vectorEffect="non-scaling-stroke"
              />
            </g>
          </svg>
        ) : (
          <div className={clsx("grid place-items-center border border-[rgba(255,118,99,0.46)] bg-[rgba(31,9,9,0.86)]", svgClasses)}>
            <div className="text-center">
              <div className="text-[0.56rem] font-black uppercase tracking-[0.34em] text-[rgba(255,210,201,0.7)]">No Shape Bundle</div>
              <div className="mt-4 text-4xl font-black uppercase tracking-[0.16em] text-[#fff0eb]">{iso3 ?? title.slice(0, 3)}</div>
            </div>
          </div>
        )}
      </div>
      {label ? (
        <div
          className="absolute bottom-4 left-4 border px-4 py-3"
          style={{
            borderColor: "rgba(255,118,99,0.68)",
            background: "rgba(42, 10, 10, 0.94)",
            boxShadow: "inset 0 1px 0 rgba(255, 118, 99, 0.24)",
          }}
        >
          <div className="text-[0.52rem] font-black uppercase tracking-[0.32em] text-[rgba(255,210,201,0.72)]">Locator Plate</div>
          <div className="mt-1 text-[0.74rem] font-black uppercase tracking-[0.24em] text-[#fff0eb]">{label}</div>
        </div>
      ) : null}
    </div>
  );
}
