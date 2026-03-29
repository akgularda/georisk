import Link from "next/link";
import { RiskBadge } from "@/components/risk-badge";
import type { CountryProfile } from "@/lib/types";

interface GlobalContextStripProps {
  countries: CountryProfile[];
}

export function GlobalContextStrip({ countries }: GlobalContextStripProps) {
  return (
    <div className="grid gap-4 lg:grid-cols-5">
      {countries.map((country) => (
        <Link
          key={country.slug}
          href={`/countries/${country.slug}`}
          className="rounded-[1.4rem] border border-black/5 bg-white/80 p-4 transition-transform hover:-translate-y-0.5"
        >
          <p className="text-[0.68rem] uppercase tracking-[0.22em] text-muted">{country.region}</p>
          <h3 className="mt-3 text-lg font-semibold tracking-[-0.03em] text-foreground">{country.name}</h3>
          <div className="mt-4">
            <RiskBadge category={country.riskCategory} score={country.riskScore} />
          </div>
        </Link>
      ))}
    </div>
  );
}
