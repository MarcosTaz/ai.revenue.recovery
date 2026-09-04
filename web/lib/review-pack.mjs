export function buildSyntheticReviewPack({ organizationId, finding, review }) {
  if (!organizationId || typeof organizationId !== 'string') {
    throw new Error('organizationId is required');
  }
  if (!finding || !finding.findingId || !finding.state) {
    throw new Error('finding identity and state are required');
  }

  const approvedRecoveryCandidates = [];
  const payableExposures = [];
  const unresolved = [];

  if (finding.state === 'RECOVERY_CANDIDATE') {
    if (review?.decision === 'APPROVED' && review?.reviewerId && review?.rationale) {
      approvedRecoveryCandidates.push(finding);
    } else {
      unresolved.push(finding);
    }
  } else if (finding.state === 'PAYABLE_CANDIDATE') {
    payableExposures.push(finding);
  } else if (['UNKNOWN', 'REQUIRES_REVIEW'].includes(finding.state)) {
    unresolved.push(finding);
  }

  let status = 'NO_RECOVERY_PACK';
  if (approvedRecoveryCandidates.length) status = 'READY_FOR_CLIENT_FINANCE_REVIEW';
  else if (finding.state === 'RECOVERY_CANDIDATE') status = 'DRAFT';

  return {
    organizationId,
    status,
    approvedRecoveryCandidates,
    payableExposures,
    unresolved,
    reviewLog: review ? [review] : [],
  };
}
