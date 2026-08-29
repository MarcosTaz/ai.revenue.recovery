"use client";

import { useMemo, useState } from "react";
import { computeAssuranceSnapshot } from "../lib/assurance.mjs";

const usd = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 });

export function AssuranceDemo() {
  const [expected, setExpected] = useState("1000000");
  const [billed, setBilled] = useState("920000");
  const [paid, setPaid] = useState("900000");
  const [fundingSupported, setFundingSupported] = useState(true);
  const [ceilingSupported, setCeilingSupported] = useState(true);
  const [proceduralRisk, setProceduralRisk] = useState(false);

  const snapshot = useMemo(() => computeAssuranceSnapshot({
    supportedExpectedBilling: Number(expected),
    cumulativeBilled: Number(billed),
    cumulativePaid: Number(paid),
    evidenceComplete: true,
    contractTermsSupported: true,
    allowabilitySupported: true,
    allocabilitySupported: true,
    fundingSupported,
    ceilingSupported,
    finalRateSettledWhenRequired: true,
    proceduralRisk,
    expresslyUnallowable: false,
  }), [expected, billed, paid, fundingSupported, ceilingSupported, proceduralRisk]);

  const stateClass = snapshot.state === "SUPPORTED_UNBILLED"
    ? "status-positive"
    : snapshot.state === "PAYABLE_EXPOSURE"
      ? "status-negative"
      : snapshot.state === "CURRENT"
        ? "status-neutral"
        : "status-review";

  return (
    <section className="panel evidence-panel" aria-labelledby="assurance-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Continuous assurance — synthetic</p>
          <h2 id="assurance-title">Earned / billed / paid monitor</h2>
        </div>
        <span className="badge">Fail closed</span>
      </div>
      <div className="calculator-grid">
        <label>
          Supported expected billing
          <input value={expected} onChange={(event) => setExpected(event.target.value)} inputMode="decimal" />
        </label>
        <label>
          Cumulative billed
          <input value={billed} onChange={(event) => setBilled(event.target.value)} inputMode="decimal" />
        </label>
        <label>
          Verified paid
          <input value={paid} onChange={(event) => setPaid(event.target.value)} inputMode="decimal" />
        </label>
        <div className="checks" role="group" aria-label="Assurance gates">
          <label><input type="checkbox" checked={fundingSupported} onChange={(event) => setFundingSupported(event.target.checked)} /> Funding supported</label>
          <label><input type="checkbox" checked={ceilingSupported} onChange={(event) => setCeilingSupported(event.target.checked)} /> Ceiling supported</label>
          <label><input type="checkbox" checked={proceduralRisk} onChange={(event) => setProceduralRisk(event.target.checked)} /> Procedural risk present</label>
        </div>
      </div>
      <div className={`result ${stateClass}`} aria-live="polite">
        <div><span>Assurance state</span><strong>{snapshot.state.replaceAll("_", " ")}</strong></div>
        <div><span>Supported earned</span><strong>{snapshot.earnedSupported == null ? "—" : usd.format(snapshot.earnedSupported)}</strong></div>
        <div><span>Supported unbilled</span><strong>{snapshot.supportedUnbilled == null ? "—" : usd.format(snapshot.supportedUnbilled)}</strong></div>
        <div><span>Payment shortfall</span><strong>{snapshot.paymentShortfall == null ? "—" : usd.format(snapshot.paymentShortfall)}</strong></div>
        <div><span>Payable exposure</span><strong>{snapshot.payableExposure == null ? "—" : usd.format(snapshot.payableExposure)}</strong></div>
        <p>{snapshot.explanation}</p>
      </div>
    </section>
  );
}
