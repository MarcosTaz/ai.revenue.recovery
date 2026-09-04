-- DebtRecover v0.4.4 additive Data API / JWT RLS delta.
-- Synthetic branch only. Existing backend policies remain untouched.

CREATE OR REPLACE FUNCTION debtrecover.has_org_access(target_org uuid) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = pg_catalog, debtrecover
AS $$
  SELECT auth.user_id() IS NOT NULL
     AND EXISTS (
       SELECT 1 FROM debtrecover.memberships m
       WHERE m.organization_id = target_org
         AND m.user_subject = auth.user_id()
     )
$$;

CREATE OR REPLACE FUNCTION debtrecover.has_org_role(target_org uuid, allowed_roles text[]) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = pg_catalog, debtrecover
AS $$
  SELECT auth.user_id() IS NOT NULL
     AND EXISTS (
       SELECT 1 FROM debtrecover.memberships m
       WHERE m.organization_id = target_org
         AND m.user_subject = auth.user_id()
         AND m.role = ANY (allowed_roles)
     )
$$;

REVOKE ALL ON FUNCTION debtrecover.has_org_access(uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION debtrecover.has_org_role(uuid, text[]) FROM PUBLIC;

GRANT USAGE ON SCHEMA debtrecover TO authenticated;
GRANT EXECUTE ON FUNCTION debtrecover.has_org_access(uuid), debtrecover.has_org_role(uuid, text[]) TO authenticated;
GRANT SELECT ON debtrecover.organizations, debtrecover.memberships TO authenticated;
GRANT SELECT, INSERT, UPDATE ON debtrecover.cases TO authenticated;
GRANT SELECT, INSERT ON debtrecover.evidence_metadata, debtrecover.findings, debtrecover.outcomes, debtrecover.audit_log TO authenticated;

CREATE POLICY org_select_authenticated ON debtrecover.organizations FOR SELECT TO authenticated
  USING (debtrecover.has_org_access(id));
CREATE POLICY membership_select_authenticated ON debtrecover.memberships FOR SELECT TO authenticated
  USING (debtrecover.has_org_access(organization_id));

CREATE POLICY case_select_authenticated ON debtrecover.cases FOR SELECT TO authenticated
  USING (debtrecover.has_org_access(organization_id));
CREATE POLICY case_insert_authenticated ON debtrecover.cases FOR INSERT TO authenticated
  WITH CHECK (debtrecover.has_org_role(organization_id, ARRAY['OWNER','ANALYST']));
CREATE POLICY case_update_authenticated ON debtrecover.cases FOR UPDATE TO authenticated
  USING (debtrecover.has_org_role(organization_id, ARRAY['OWNER','ANALYST']))
  WITH CHECK (debtrecover.has_org_role(organization_id, ARRAY['OWNER','ANALYST']));

CREATE POLICY evidence_select_authenticated ON debtrecover.evidence_metadata FOR SELECT TO authenticated
  USING (debtrecover.has_org_access(organization_id));
CREATE POLICY evidence_insert_authenticated ON debtrecover.evidence_metadata FOR INSERT TO authenticated
  WITH CHECK (debtrecover.has_org_role(organization_id, ARRAY['OWNER','ANALYST']));

CREATE POLICY finding_select_authenticated ON debtrecover.findings FOR SELECT TO authenticated
  USING (debtrecover.has_org_access(organization_id));
CREATE POLICY finding_insert_authenticated ON debtrecover.findings FOR INSERT TO authenticated
  WITH CHECK (debtrecover.has_org_role(organization_id, ARRAY['OWNER','ANALYST','REVIEWER']));

CREATE POLICY outcome_select_authenticated ON debtrecover.outcomes FOR SELECT TO authenticated
  USING (debtrecover.has_org_access(organization_id));
CREATE POLICY outcome_insert_authenticated ON debtrecover.outcomes FOR INSERT TO authenticated
  WITH CHECK (debtrecover.has_org_role(organization_id, ARRAY['OWNER','REVIEWER']));

CREATE POLICY audit_select_authenticated ON debtrecover.audit_log FOR SELECT TO authenticated
  USING (debtrecover.has_org_access(organization_id));
CREATE POLICY audit_insert_authenticated ON debtrecover.audit_log FOR INSERT TO authenticated
  WITH CHECK (debtrecover.has_org_access(organization_id));
