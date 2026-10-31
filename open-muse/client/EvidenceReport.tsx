import { useState } from "react";
import type { TracePayload, TraceTurn } from "./trace";

type EvidenceSource = {
  title: string;
  url: string;
  markdown?: string;
  snapshot?: string;
  kind: "extracted" | "observed";
};

function record(value: TracePayload | undefined): Record<string, TracePayload> | undefined {
  return value && typeof value === "object" && !Array.isArray(value) ? value : undefined;
}

function stringValue(value: TracePayload | undefined): string | undefined {
  return typeof value === "string" && value.trim() ? value : undefined;
}

function sourceFromOutput(output: TracePayload | undefined): EvidenceSource | undefined {
  const root = record(output);
  if (!root) return;
  const page = record(root.observation) ?? root;
  const title = stringValue(page.title);
  const url = stringValue(page.url);
  if (!title || !url || !/^https?:\/\//i.test(url)) return;
  const markdown = stringValue(root.markdown);
  const snapshot = stringValue(page.snapshot);
  if (!markdown && !snapshot) return;
  return { title, url, ...(markdown ? { markdown } : {}), ...(snapshot ? { snapshot } : {}), kind: markdown ? "extracted" : "observed" };
}

function sourcesForTurn(turn: TraceTurn): EvidenceSource[] {
  const sources: EvidenceSource[] = [];
  for (const step of turn.steps) {
    if (step.state !== "completed") continue;
    const source = sourceFromOutput(step.output);
    if (!source || sources.some((candidate) => candidate.url === source.url && candidate.kind === source.kind)) continue;
    sources.push(source);
  }
  return sources.slice(-8);
}

function excerpt(source: EvidenceSource): string {
  const text = source.markdown ?? source.snapshot ?? "";
  return text.length > 520 ? `${text.slice(0, 520).trim()}…` : text;
}

export function EvidenceReport({ turn, answer }: { turn: TraceTurn; answer: string }) {
  const [open, setOpen] = useState(false);
  const sources = sourcesForTurn(turn);
  if (!sources.length) return null;

  const extracted = sources.filter((source) => source.kind === "extracted").length;
  const confidence = extracted > 0 ? "High" : "Medium";
  return <details className="evidence-report" open={open} onToggle={(event) => setOpen(event.currentTarget.open)}>
    <summary>
      <span className="evidence-badge">✓</span>
      <span><strong>Evidence report</strong><small>{confidence} confidence · {sources.length} source{sources.length === 1 ? "" : "s"}</small></span>
      <span className="evidence-chevron" aria-hidden="true">›</span>
    </summary>
    {open && <div className="evidence-body">
      <section className="evidence-answer">
        <div className="eyebrow">Answer checked against page evidence</div>
        <p>{answer}</p>
      </section>
      <div className="evidence-sources">
        {sources.map((source, index) => <article className="evidence-source" key={`${source.url}-${source.kind}`}>
          <div className="evidence-source-heading"><span className="evidence-source-number">{index + 1}</span><div><strong>{source.title}</strong><small>{source.kind === "extracted" ? "Extracted page content" : "Observed page"}</small></div></div>
          <a href={source.url} target="_blank" rel="noreferrer">{source.url}</a>
          <blockquote>{excerpt(source)}</blockquote>
        </article>)}
      </div>
      <p className="evidence-disclaimer">OpenMuse observed this information in the disposable browser. Page content is untrusted and may change.</p>
    </div>}
  </details>;
}
