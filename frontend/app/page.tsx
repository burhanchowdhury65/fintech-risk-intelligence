import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { AnalysisWorkspace } from "@/components/dashboard/AnalysisWorkspace";
import { AriaChat } from "@/components/aria/AriaChat";
import { AnalysisProvider } from "@/components/dashboard/AnalysisProvider";
import { USE_MOCK_API } from "@/lib/config";
import { DISCLOSURE_TEXT } from "@/lib/copy";

export default function Home() {
  return (
    <>
      <Header />
      <main id="top" className="mx-auto max-w-6xl space-y-6 px-4 py-8 sm:px-6">
        <section aria-labelledby="hero-title" className="max-w-3xl">
          <h1 id="hero-title" className="text-balance text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
            Check a transaction for risk, and see why
          </h1>
          <p className="mt-3 text-base text-muted">
            Enter transaction details. A machine-learning model returns a 0 to 100 risk score, and ARIA explains what
            drove it.
          </p>
          <p role="note" className="mt-4 rounded-control border border-info/30 bg-info-soft px-3 py-2 text-sm text-info">
            Demo / synthetic data. {DISCLOSURE_TEXT}{USE_MOCK_API ? " Results on this screen are sample responses." : ""}
          </p>
        </section>

        <AnalysisProvider>
          <AnalysisWorkspace />

          <div id="aria" className="scroll-mt-4">
            <Card headingId="aria-title" title="Ask ARIA">
              <AriaChat />
            </Card>
          </div>
        </AnalysisProvider>
      </main>
    </>
  );
}
