from __future__ import annotations
from dataclasses import dataclass
from urllib.parse import urlparse
from production_security import ProductionSecrets


def _https(value:str)->bool:
    try:
        u=urlparse(value); return u.scheme=='https' and bool(u.netloc)
    except Exception: return False

@dataclass(frozen=True)
class DeploymentReadiness:
    checks: dict[str,bool]
    blockers: tuple[str,...]
    accept_real_borrower_data: bool
    def as_dict(self)->dict:
        return {'checks':dict(self.checks),'blockers':list(self.blockers),'accept_real_borrower_data':self.accept_real_borrower_data}


def evaluate_deployment_readiness(env:dict)->DeploymentReadiness:
    checks={}
    try:
        ProductionSecrets.from_env(env); checks['independent_secrets']=True
    except Exception:
        checks['independent_secrets']=False
    checks['oidc_issuer_https']=_https(str(env.get('DEBTRECOVER_OIDC_ISSUER','')))
    checks['oidc_audience']=bool(str(env.get('DEBTRECOVER_OIDC_AUDIENCE','')).strip())
    checks['oidc_jwks_https']=_https(str(env.get('DEBTRECOVER_OIDC_JWKS_URL','')))
    checks['public_base_https']=_https(str(env.get('DEBTRECOVER_PUBLIC_BASE_URL','')))
    checks['audit_anchor_https']=_https(str(env.get('DEBTRECOVER_AUDIT_ANCHOR_URL','')))
    for key,label in (
        ('DEBTRECOVER_OBJECT_STORAGE_PROVIDER','durable_object_storage_provider'),
        ('DEBTRECOVER_KMS_PROVIDER','kms_provider'),
        ('DEBTRECOVER_SECRET_MANAGER_PROVIDER','secret_manager_provider'),
        ('DEBTRECOVER_MALWARE_SCANNER_PROVIDER','malware_scanner_provider'),
        ('DEBTRECOVER_MONITORING_PROVIDER','monitoring_provider'),
        ('DEBTRECOVER_BACKUP_PROVIDER','backup_provider'),
    ):
        checks[label]=bool(str(env.get(key,'')).strip())
    checks['benchmark_rights_approved']=str(env.get('DEBTRECOVER_BENCHMARK_RIGHTS_STATE','')).upper()=='APPROVED_FOR_PRODUCTION'
    checks['legal_review_approved']=str(env.get('DEBTRECOVER_LEGAL_REVIEW_STATE','')).upper() in {'APPROVED_FOR_ASSISTED_PILOT','APPROVED_FOR_PRODUCTION'}
    blockers=tuple(k for k,v in checks.items() if not v)
    return DeploymentReadiness(checks,blockers,not blockers)


def require_real_data_ready(env:dict)->DeploymentReadiness:
    r=evaluate_deployment_readiness(env)
    if not r.accept_real_borrower_data:
        raise RuntimeError('real borrower data gate failed: '+','.join(r.blockers))
    return r
