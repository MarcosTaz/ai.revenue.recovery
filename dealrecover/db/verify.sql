\set ON_ERROR_STOP on

DO $$
DECLARE
  required text[] := ARRAY['tenants','memberships','deals','documents','analyses','dossiers','dispute_events','outcomes','audit_events','billing','document_blobs','api_sessions'];
  n int;
BEGIN
  SELECT count(*) INTO n FROM information_schema.tables WHERE table_schema='public' AND table_name = ANY(required);
  IF n <> 12 THEN RAISE EXCEPTION 'DealRecover schema incomplete: %/12 tables', n; END IF;

  SELECT count(*) INTO n
  FROM pg_class c JOIN pg_namespace ns ON ns.oid=c.relnamespace
  WHERE ns.nspname='public' AND c.relname = ANY(required) AND c.relrowsecurity AND c.relforcerowsecurity;
  IF n <> 12 THEN RAISE EXCEPTION 'DealRecover FORCE RLS incomplete: %/12 tables', n; END IF;

  SELECT count(*) INTO n FROM pg_policies
  WHERE schemaname='public' AND tablename = ANY(required) AND policyname='tenant_isolation';
  IF n <> 12 THEN RAISE EXCEPTION 'DealRecover tenant policies incomplete: %/12', n; END IF;

  IF has_table_privilege('dealrecover_rls','public.audit_events','UPDATE') OR has_table_privilege('dealrecover_rls','public.audit_events','DELETE') THEN
    RAISE EXCEPTION 'audit_events must be append-only to dealrecover_rls';
  END IF;
  IF has_table_privilege('dealrecover_rls','public.api_sessions','INSERT') THEN
    RAISE EXCEPTION 'runtime must not mint API sessions';
  END IF;
  IF has_table_privilege('dealrecover_rls','public.document_blobs','UPDATE') OR has_table_privilege('dealrecover_rls','public.document_blobs','DELETE') THEN
    RAISE EXCEPTION 'document blobs must not be mutable by runtime';
  END IF;
  IF NOT has_sequence_privilege('dealrecover_rls','public.dispute_events_id_seq','USAGE') OR NOT has_sequence_privilege('dealrecover_rls','public.audit_events_seq_seq','USAGE') THEN
    RAISE EXCEPTION 'runtime sequence privileges incomplete';
  END IF;
  IF NOT has_function_privilege('dealrecover_rls','public.app_tenant_id()','EXECUTE') OR has_function_privilege('public','public.app_tenant_id()','EXECUTE') THEN
    RAISE EXCEPTION 'app_tenant_id execute grants invalid';
  END IF;
END $$;

BEGIN;
SET LOCAL ROLE dealrecover_rls;
SELECT set_config('app.tenant_id','99999999-9999-4999-8999-999999999999',true);
INSERT INTO public.tenants(id,name) VALUES('99999999-9999-4999-8999-999999999999','Verification Tenant A');
INSERT INTO public.memberships(tenant_id,user_id,role) VALUES('99999999-9999-4999-8999-999999999999','88888888-8888-4888-8888-888888888888','OWNER');
INSERT INTO public.deals(tenant_id,id,counterparty,currency) VALUES('99999999-9999-4999-8999-999999999999','77777777-7777-4777-8777-777777777777','Verification Seller','EUR');
DO $$ DECLARE n int; BEGIN SELECT count(*) INTO n FROM public.deals WHERE id='77777777-7777-4777-8777-777777777777'; IF n <> 1 THEN RAISE EXCEPTION 'tenant A cannot see its deal'; END IF; END $$;
SELECT set_config('app.tenant_id','66666666-6666-4666-8666-666666666666',true);
DO $$ DECLARE n int; BEGIN SELECT count(*) INTO n FROM public.deals WHERE id='77777777-7777-4777-8777-777777777777'; IF n <> 0 THEN RAISE EXCEPTION 'cross-tenant isolation failed'; END IF; END $$;
ROLLBACK;

SELECT 'DEALRECOVER_DB_VERIFY_PASS' AS result;
