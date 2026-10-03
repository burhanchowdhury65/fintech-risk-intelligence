import type { ReactNode } from "react";

interface CardProps {
  title: string;
  description?: string;
  headingId: string;
  children: ReactNode;
  className?: string;
}

export function Card({ title, description, headingId, children, className = "" }: CardProps) {
  return (
    <section
      aria-labelledby={headingId}
      className={`rounded-card border border-line bg-surface p-5 shadow-card sm:p-6 ${className}`}
    >
      <h2 id={headingId} className="text-lg font-semibold text-ink">
        {title}
      </h2>
      {description && <p className="mt-1 max-w-prose text-sm text-muted">{description}</p>}
      <div className="mt-4">{children}</div>
    </section>
  );
}
