import { TrueUpCalculator } from "./true-up-calculator";

const controls = [
  ["Contract applicability", "Clause + version gated"],
  ["Rate status", "Settled final only"],
  ["Cost treatment", "Allowability + allocability"],
  ["Limitations", "Ceiling + funding checked"],
  ["Prior billing", "Cumulative, not incremental guess"],
  ["Outcome truth", "Receivable and payable symmetric"],
];

export default function Home() {
  return (
    <main>
      <header className="topbar">
        <div className="brand-mark">GM</div>
        <div className="brand-copy">
          <strong>GovMargin</strong>
          <span>Government Contract Economic Assurance</span>
        </div>
        <div className="topbar-status"><span /> Synthetic workspace</div>
      </header>

      <section className="hero">
        <p className="eyebrow">Earned → billed → paid</p>
        <h1>Reconstruct contract economics before calling anything a recovery.</h1>
        <p className="hero-copy">
          GovMargin is an independent contractor-side reconciliation layer for flexibly priced U.S. federal contracts. It is designed to surface legitimate underbilling, overbilling, limitations and unknowns with evidence lineage.
        </p>
        <div className="truth-strip">
          <div><span>Current validation</span><strong>Materiality open</strong></div>
          <div><span>Initial wedge</span><strong>Final-rate true-up</strong></div>
          <div><span>Rule posture</span><strong>Fail closed</strong></div>
          <div><span>Commercial state</span><strong>Pre-pilot</strong></div>
        </div>
      </section>

      <section className="content-grid">
        <div className="panel assurance-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Assurance gates</p>
              <h2>Nothing becomes “due” from arithmetic alone.</h2>
            </div>
          </div>
          <div className="control-list">
            {controls.map(([name, value]) => (
              <div className="control-row" key={name}>
                <span>{name}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
          <div className="notice">
            This prototype is a synthetic analysis surface, not legal advice, a certified claim, an accounting attestation, or an assertion that the Government owes money.
          </div>
        </div>

        <TrueUpCalculator />
      </section>

      <section className="panel evidence-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Evidence lineage</p>
            <h2>Current verified rule anchors</h2>
          </div>
        </div>
        <div className="rule-grid">
          <article><span>FAR 52.216-7(d)(2)(v)</span><strong>Update billings after final-rate settlement</strong><p>Current rule entry is clause/version gated; historic contracts do not inherit it automatically.</p></article>
          <article><span>FAR 52.216-7(d)(5)</span><strong>Completion invoice / voucher</strong><p>Timing and final-rate settlement are represented as evidence requirements, not assumptions.</p></article>
          <article><span>FAR 52.216-7(e)</span><strong>Billing-rate adjustment</strong><p>Underpayment and overpayment are treated symmetrically and remain subject to contract limits.</p></article>
        </div>
      </section>
    </main>
  );
}
