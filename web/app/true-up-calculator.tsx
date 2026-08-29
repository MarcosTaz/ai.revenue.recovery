"use client";

import { FormEvent, useMemo, useState } from "react";
import { computeIndirectTrueUp } from "../lib/true-up.mjs";
import { evaluateFundingSafeguard } from "../lib/funding.mjs";

type Result = {
  state: string;
  expectedIndirect: number | null;
  variance: number | null;
  explanation: string;
};

type FundingResult = {
  state: string;
  verifiedLimit?: number;
  projectedCostAtNoticeWindow?: number;
  thresholdAmount?: number;
  automaticRecoveryAllowed: boolean;
  explanation: string;
};

const usd = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 });

export function TrueUpCalculator() {
  const [allocationBase, setAllocationBase] = useState("1000000");
  const [finalRatePct, setFinalRatePct] = useState("25");
  const [billedIndirect, setBilledIndirect] = useState("200000");
  const [ceiling, setCeiling] = useState("");
  const [funding, setFunding] = useState("100000");
  const [fundingClause, setFundingClause] = useState("52.232-22");
  const [estimatedCost, setEstimatedCost] = useState("1200000");
  const [allottedFunds, setAllottedFunds] = useState("1100000");
  const [costsIncurred, setCostsIncurred] = useState("700000");
  const [nextWindowCosts, setNextWindowCosts] = useState("100000");
  const [noticeThresholdPct, setNoticeThresholdPct] = useState("75");
  const [noticeWindowDays, setNoticeWindowDays] = useState("60");
  const [settled, setSettled] = useState(true);
  const [termsVerified, setTermsVerified] = useState(true);
  const [allowability, setAllowability] = useState(true);
  const [allocability, setAllocability] = useState(true);
  const [result, setResult] = useState<Result | null>(null);
  const [fundingResult, setFundingResult] = useState<FundingResult | null>(null);

  const stateClass = useMemo(() => {
    if (!result) return "status-neutral";
    if (result.state === "RECOVERY_CANDIDATE") return "status-positive";
    if (result.state === "PAYABLE_CANDIDATE") return "status-negative";
    if (result.state === "UNKNOWN" || result.state === "REQUIRES_REVIEW") return "status-review";
    return "status-neutral";
  }, [result]);

  function submit(event: FormEvent) {
    event.preventDefault();
    setResult(
      computeIndirectTrueUp({
        allocationBase: Number(allocationBase),
        finalRate: Number(finalRatePct) / 100,
        billedIndirect: Number(billedIndirect),
        contractTermsVerified: termsVerified,
        finalRateSettled: settled,
        allowabilitySupported: allowability,
        allocabilitySupported: allocability,
        indirectCeilingAmount: ceiling === "" ? null : Number(ceiling),
        remainingFunding: funding === "" ? null : Number(funding),
      }) as Result,
    );
    setFundingResult(
      evaluateFundingSafeguard({
        clause: fundingClause,
        costsIncurred: Number(costsIncurred),
        expectedNextNoticeWindowCosts: Number(nextWindowCosts),
        estimatedCost: estimatedCost === "" ? null : Number(estimatedCost),
        allottedFunds: allottedFunds === "" ? null : Number(allottedFunds),
        noticeThresholdPercent: Number(noticeThresholdPct) / 100,
        noticeWindowDays: Number(noticeWindowDays),
      }) as FundingResult,
    );
  }

  return (
    <section className="panel calculator-panel" aria-labelledby="calculator-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Synthetic contract tool</p>
          <h2 id="calculator-title">Settled indirect-rate true-up</h2>
        </div>
        <span className="badge">Deterministic</span>
      </div>

      <form onSubmit={submit} className="calculator-grid">
        <label>
          Allocation base
          <input value={allocationBase} onChange={(e) => setAllocationBase(e.target.value)} inputMode="decimal" />
        </label>
        <label>
          Settled final rate (%)
          <input value={finalRatePct} onChange={(e) => setFinalRatePct(e.target.value)} inputMode="decimal" />
        </label>
        <label>
          Cumulative billed indirect
          <input value={billedIndirect} onChange={(e) => setBilledIndirect(e.target.value)} inputMode="decimal" />
        </label>
        <label>
          Indirect ceiling (optional)
          <input value={ceiling} onChange={(e) => setCeiling(e.target.value)} inputMode="decimal" placeholder="No ceiling entered" />
        </label>
        <label>
          Verified remaining funding (true-up cap check)
          <input value={funding} onChange={(e) => setFunding(e.target.value)} inputMode="decimal" />
        </label>

        <div className="checks" role="group" aria-label="Evidence gates">
          <label><input type="checkbox" checked={settled} onChange={(e) => setSettled(e.target.checked)} /> Final rate settled</label>
          <label><input type="checkbox" checked={termsVerified} onChange={(e) => setTermsVerified(e.target.checked)} /> Contract terms verified</label>
          <label><input type="checkbox" checked={allowability} onChange={(e) => setAllowability(e.target.checked)} /> Allowability supported</label>
          <label><input type="checkbox" checked={allocability} onChange={(e) => setAllocability(e.target.checked)} /> Allocability supported</label>
        </div>

        <div className="panel-heading">
          <div>
            <p className="eyebrow">Funding safeguard</p>
            <h2>Notice / limit check</h2>
          </div>
        </div>
        <label>
          Funding clause
          <select value={fundingClause} onChange={(e) => setFundingClause(e.target.value)}>
            <option value="52.232-22">FAR 52.232-22 — Limitation of Funds</option>
            <option value="52.232-20">FAR 52.232-20 — Limitation of Cost</option>
          </select>
        </label>
        <label>
          Estimated cost (52.232-20)
          <input value={estimatedCost} onChange={(e) => setEstimatedCost(e.target.value)} inputMode="decimal" />
        </label>
        <label>
          Actually allotted funds (52.232-22)
          <input value={allottedFunds} onChange={(e) => setAllottedFunds(e.target.value)} inputMode="decimal" />
        </label>
        <label>
          Costs incurred
          <input value={costsIncurred} onChange={(e) => setCostsIncurred(e.target.value)} inputMode="decimal" />
        </label>
        <label>
          Expected costs in notice window
          <input value={nextWindowCosts} onChange={(e) => setNextWindowCosts(e.target.value)} inputMode="decimal" />
        </label>
        <label>
          Contract notice threshold (%)
          <input value={noticeThresholdPct} onChange={(e) => setNoticeThresholdPct(e.target.value)} inputMode="decimal" />
        </label>
        <label>
          Contract notice window (days)
          <input value={noticeWindowDays} onChange={(e) => setNoticeWindowDays(e.target.value)} inputMode="numeric" />
        </label>

        <button className="primary-button" type="submit">Reconcile synthetic case</button>
      </form>

      {result && (
        <div className={`result ${stateClass}`} aria-live="polite">
          <div>
            <span>True-up result</span>
            <strong>{result.state.replaceAll("_", " ")}</strong>
          </div>
          <div>
            <span>Expected indirect</span>
            <strong>{result.expectedIndirect === null ? "—" : usd.format(result.expectedIndirect)}</strong>
          </div>
          <div>
            <span>Variance</span>
            <strong>{result.variance === null ? "—" : usd.format(result.variance)}</strong>
          </div>
          <p>{result.explanation}</p>
        </div>
      )}

      {fundingResult && (
        <div className="result status-review" aria-live="polite">
          <div>
            <span>Funding safeguard</span>
            <strong>{fundingResult.state.replaceAll("_", " ")}</strong>
          </div>
          <div>
            <span>Verified limit</span>
            <strong>{fundingResult.verifiedLimit === undefined ? "—" : usd.format(fundingResult.verifiedLimit)}</strong>
          </div>
          <div>
            <span>Automatic recovery</span>
            <strong>{fundingResult.automaticRecoveryAllowed ? "YES" : "NO"}</strong>
          </div>
          <p>{fundingResult.explanation}</p>
        </div>
      )}
    </section>
  );
}
