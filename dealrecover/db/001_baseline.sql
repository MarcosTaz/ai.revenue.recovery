-- DealRecover v0.7.3.1 database baseline
-- Database-scoped migration. Platform roles are provisioned separately in Neon.
-- Fail closed: the runtime roles must already exist, be non-privileged, and runtime must be able to SET ROLE dealrecover_rls.

BEGIN;

DO $$
DECLARE
  r record;
BEGIN
  SELECT rolname, rolcanlogin, rolsuper, rolinherit, rolcreaterole, rolcreatedb, rolreplication, rolbypassrls
    INTO r FROM pg_roles WHERE rolname = 'dealrecover_rls';
  IF NOT FOUND THEN RAISE EXCEPTION 'required platform role dealrecover_rls missing'; END IF;
  IF r.rolcanlogin OR r.rolsuper OR r.rolinherit OR r.rolcreaterole OR r.rolcreatedb OR r.rolreplication OR r.rolbypassrls THEN
    RAISE EXCEPTION 'dealrecover_rls role is not least-privilege safe';
  END IF;

  SELECT rolname, rolcanlogin, rolsuper, rolinherit, rolcreaterole, rolcreatedb, rolreplication, rolbypassrls
    INTO r FROM pg_roles WHERE rolname = 'dealrecover_runtime';
  IF NOT FOUND THEN RAISE EXCEPTION 'required platform role dealrecover_runtime missing'; END IF;
  IF NOT r.rolcanlogin OR r.rolsuper OR r.rolinherit OR r.rolcreaterole OR r.rolcreatedb OR r.rolreplication OR r.rolbypassrls THEN
    RAISE EXCEPTION 'dealrecover_runtime role is not least-privilege safe';
  END IF;

  IF NOT pg_has_role('dealrecover_runtime', 'dealrecover_rls', 'MEMBER') THEN
    RAISE EXCEPTION 'dealrecover_runtime must be a member of dealrecover_rls';
  END IF;
END $$;

CREATE OR REPLACE FUNCTION public.app_tenant_id()
RETURNS text
LANGUAGE sql
STABLE
AS $$ SELECT nullif(current_setting('app.tenant_id', true), '') $$;

CREATE TABLE public.tenants (
  id text PRIMARY KEY,
  name text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.memberships (
  tenant_id text NOT NULL,
  user_id text NOT NULL,
  role text NOT NULL CHECK (role = ANY (ARRAY['OWNER'::text,'ANALYST'::text,'REVIEWER'::text])),
  PRIMARY KEY (tenant_id,user_id),
  FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE
);

CREATE TABLE public.deals (
  tenant_id text NOT NULL,
  id text NOT NULL,
  counterparty text,
  currency text NOT NULL CHECK (currency ~ '^[A-Z]{3}$'::text),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id,id),
  FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE,
  UNIQUE (tenant_id,id,currency)
);

CREATE TABLE public.documents (
  tenant_id text NOT NULL,
  deal_id text NOT NULL,
  id text NOT NULL,
  kind text NOT NULL,
  sha256 char(64) NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'::text),
  storage_key text NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id,deal_id,id),
  FOREIGN KEY (tenant_id,deal_id) REFERENCES public.deals(tenant_id,id) ON DELETE CASCADE,
  UNIQUE (tenant_id,deal_id,sha256)
);
CREATE INDEX document_lookup_idx ON public.documents (tenant_id,deal_id,kind);

CREATE TABLE public.analyses (
  tenant_id text NOT NULL,
  deal_id text NOT NULL,
  digest char(64) NOT NULL CHECK (digest ~ '^[0-9a-f]{64}$'::text),
  payload jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id,deal_id,digest),
  FOREIGN KEY (tenant_id,deal_id) REFERENCES public.deals(tenant_id,id) ON DELETE CASCADE
);
CREATE INDEX analysis_recent_idx ON public.analyses (tenant_id,deal_id,created_at DESC);

CREATE TABLE public.dossiers (
  tenant_id text NOT NULL,
  deal_id text NOT NULL,
  digest char(64) NOT NULL CHECK (digest ~ '^[0-9a-f]{64}$'::text),
  payload jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id,deal_id,digest),
  FOREIGN KEY (tenant_id,deal_id,digest) REFERENCES public.analyses(tenant_id,deal_id,digest) ON DELETE CASCADE
);

CREATE TABLE public.dispute_events (
  id bigserial PRIMARY KEY,
  tenant_id text NOT NULL,
  deal_id text NOT NULL,
  state text NOT NULL CHECK (state = ANY (ARRAY['NOT_STARTED'::text,'REVIEWED'::text,'NOTICE_PREPARED'::text,'SUBMITTED_EXTERNALLY'::text,'RESOLVED'::text])),
  note text,
  actor_id text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (tenant_id,deal_id) REFERENCES public.deals(tenant_id,id) ON DELETE CASCADE
);
CREATE INDEX dispute_recent_idx ON public.dispute_events (tenant_id,deal_id,created_at DESC);

CREATE TABLE public.outcomes (
  tenant_id text NOT NULL,
  deal_id text NOT NULL,
  outcome text NOT NULL CHECK (outcome = ANY (ARRAY['NO_RECOVERY'::text,'SETTLED'::text,'RECOVERED'::text,'WITHDRAWN'::text])),
  amount numeric(18,2) CHECK (amount IS NULL OR amount >= 0::numeric),
  currency text CHECK (currency IS NULL OR currency ~ '^[A-Z]{3}$'::text),
  evidence_digest char(64) CHECK (evidence_digest IS NULL OR evidence_digest ~ '^[0-9a-f]{64}$'::text),
  evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  recorded_by text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id,deal_id),
  FOREIGN KEY (tenant_id,deal_id) REFERENCES public.deals(tenant_id,id) ON DELETE CASCADE,
  FOREIGN KEY (tenant_id,deal_id,currency) REFERENCES public.deals(tenant_id,id,currency)
);

CREATE TABLE public.audit_events (
  seq bigserial PRIMARY KEY,
  tenant_id text NOT NULL,
  deal_id text,
  event_type text NOT NULL,
  actor_id text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  prev_hash char(64),
  event_hash char(64) NOT NULL CHECK (event_hash ~ '^[0-9a-f]{64}$'::text),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (event_hash),
  FOREIGN KEY (tenant_id,deal_id) REFERENCES public.deals(tenant_id,id) ON DELETE CASCADE
);
CREATE INDEX audit_tenant_deal_idx ON public.audit_events (tenant_id,deal_id,seq);

CREATE TABLE public.billing (
  tenant_id text NOT NULL,
  deal_id text NOT NULL,
  status text NOT NULL CHECK (status = ANY (ARRAY['DRAFT'::text,'APPROVED_TO_INVOICE'::text,'INVOICED_EXTERNALLY'::text,'PAID_EXTERNALLY'::text,'VOID'::text])),
  amount numeric(18,2) NOT NULL DEFAULT 0 CHECK (amount >= 0::numeric),
  currency text CHECK (currency IS NULL OR currency ~ '^[A-Z]{3}$'::text),
  payment_evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id,deal_id),
  FOREIGN KEY (tenant_id,deal_id) REFERENCES public.deals(tenant_id,id) ON DELETE CASCADE,
  FOREIGN KEY (tenant_id,deal_id,currency) REFERENCES public.deals(tenant_id,id,currency)
);

CREATE TABLE public.document_blobs (
  tenant_id text NOT NULL,
  deal_id text NOT NULL,
  document_id text NOT NULL,
  storage_key text NOT NULL,
  ciphertext bytea NOT NULL CHECK (octet_length(ciphertext) >= 32),
  content_type text NOT NULL DEFAULT 'application/octet-stream'::text,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id,deal_id,document_id),
  FOREIGN KEY (tenant_id,deal_id) REFERENCES public.deals(tenant_id,id) ON DELETE CASCADE,
  UNIQUE (tenant_id,deal_id,storage_key)
);
CREATE INDEX document_blobs_lookup_idx ON public.document_blobs (tenant_id,deal_id,storage_key);

CREATE TABLE public.api_sessions (
  tenant_id text NOT NULL,
  token_hash char(64) NOT NULL CHECK (token_hash ~ '^[0-9a-f]{64}$'::text),
  user_id text NOT NULL,
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  verification_ref text NOT NULL CHECK (length(verification_ref) >= 1 AND length(verification_ref) <= 512),
  PRIMARY KEY (tenant_id,token_hash),
  FOREIGN KEY (tenant_id,user_id) REFERENCES public.memberships(tenant_id,user_id) ON DELETE CASCADE,
  CHECK (expires_at > created_at)
);
CREATE INDEX api_sessions_expiry_idx ON public.api_sessions (tenant_id,expires_at) WHERE revoked_at IS NULL;

ALTER TABLE public.tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenants FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON public.tenants FOR ALL USING (id = public.app_tenant_id()) WITH CHECK (id = public.app_tenant_id());

ALTER TABLE public.memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.memberships FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON public.memberships FOR ALL USING (tenant_id = public.app_tenant_id()) WITH CHECK (tenant_id = public.app_tenant_id());

ALTER TABLE public.deals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.deals FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON public.deals FOR ALL USING (tenant_id = public.app_tenant_id()) WITH CHECK (tenant_id = public.app_tenant_id());

ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON public.documents FOR ALL USING (tenant_id = public.app_tenant_id()) WITH CHECK (tenant_id = public.app_tenant_id());

ALTER TABLE public.analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analyses FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON public.analyses FOR ALL USING (tenant_id = public.app_tenant_id()) WITH CHECK (tenant_id = public.app_tenant_id());

ALTER TABLE public.dossiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dossiers FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON public.dossiers FOR ALL USING (tenant_id = public.app_tenant_id()) WITH CHECK (tenant_id = public.app_tenant_id());

ALTER TABLE public.dispute_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dispute_events FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON public.dispute_events FOR ALL USING (tenant_id = public.app_tenant_id()) WITH CHECK (tenant_id = public.app_tenant_id());

ALTER TABLE public.outcomes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.outcomes FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON public.outcomes FOR ALL USING (tenant_id = public.app_tenant_id()) WITH CHECK (tenant_id = public.app_tenant_id());

ALTER TABLE public.audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_events FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON public.audit_events FOR ALL USING (tenant_id = public.app_tenant_id()) WITH CHECK (tenant_id = public.app_tenant_id());

ALTER TABLE public.billing ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.billing FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON public.billing FOR ALL USING (tenant_id = public.app_tenant_id()) WITH CHECK (tenant_id = public.app_tenant_id());

ALTER TABLE public.document_blobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_blobs FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON public.document_blobs FOR ALL USING (tenant_id = public.app_tenant_id()) WITH CHECK (tenant_id = public.app_tenant_id());

ALTER TABLE public.api_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_sessions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON public.api_sessions FOR ALL USING (tenant_id = public.app_tenant_id()) WITH CHECK (tenant_id = public.app_tenant_id());

REVOKE ALL ON FUNCTION public.app_tenant_id() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.app_tenant_id() TO dealrecover_rls;
GRANT USAGE ON SCHEMA public TO dealrecover_rls;

REVOKE ALL ON public.tenants,public.memberships,public.deals,public.documents,public.analyses,public.dossiers,public.dispute_events,public.outcomes,public.audit_events,public.billing,public.document_blobs,public.api_sessions FROM PUBLIC,dealrecover_runtime,dealrecover_rls;
GRANT SELECT,INSERT ON public.tenants TO dealrecover_rls;
GRANT SELECT,INSERT,UPDATE ON public.memberships TO dealrecover_rls;
GRANT SELECT,INSERT ON public.deals TO dealrecover_rls;
GRANT SELECT,INSERT ON public.documents TO dealrecover_rls;
GRANT SELECT,INSERT ON public.analyses TO dealrecover_rls;
GRANT SELECT,INSERT ON public.dossiers TO dealrecover_rls;
GRANT SELECT,INSERT ON public.dispute_events TO dealrecover_rls;
GRANT SELECT,INSERT ON public.outcomes TO dealrecover_rls;
GRANT SELECT,INSERT ON public.audit_events TO dealrecover_rls;
GRANT SELECT,INSERT,UPDATE ON public.billing TO dealrecover_rls;
GRANT SELECT,INSERT ON public.document_blobs TO dealrecover_rls;
GRANT SELECT ON public.api_sessions TO dealrecover_rls;

REVOKE ALL ON SEQUENCE public.dispute_events_id_seq,public.audit_events_seq_seq FROM PUBLIC,dealrecover_runtime,dealrecover_rls;
GRANT USAGE ON SEQUENCE public.dispute_events_id_seq,public.audit_events_seq_seq TO dealrecover_rls;

COMMIT;
