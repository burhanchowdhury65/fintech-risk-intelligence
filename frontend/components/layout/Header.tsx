import { Badge } from "@/components/ui/Badge";
import { USE_MOCK_API } from "@/lib/config";

const nav = [
  { href: "#analyze", label: "Analyze" },
  { href: "#result", label: "Result" },
];

export function Header() {
  return (
    <header className="border-b border-line bg-surface">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
        <a href="#top" className="flex min-h-11 items-center gap-2 font-semibold text-ink">
          <span aria-hidden="true" className="grid size-8 place-items-center rounded-control bg-primary text-sm text-white">
            F
          </span>
          Fintech Risk Intelligence
        </a>
        <nav aria-label="Main" className="flex items-center gap-1 text-sm">
          {nav.map((n) => (
            <a key={n.href} href={n.href} className="inline-flex min-h-11 items-center rounded-control px-3 text-muted hover:bg-sunken hover:text-ink">
              {n.label}
            </a>
          ))}
          <a
            href="#aria"
            className="inline-flex min-h-11 items-center rounded-control bg-primary-soft px-3 font-medium text-primary hover:bg-primary-soft/70"
          >
            Ask ARIA
          </a>
        </nav>
        {USE_MOCK_API ? <Badge tone="info">Mock mode: sample data</Badge> : <Badge tone="neutral">Backend status: not checked</Badge>}
      </div>
    </header>
  );
}
