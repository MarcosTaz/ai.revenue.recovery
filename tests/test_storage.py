from govmargin.storage import ImmutableTenantStore, TenantRecord, TenantStorageError


def test_tenant_store_is_scoped_and_immutable():
    store = ImmutableTenantStore[str]()
    store.put_once(TenantRecord("org-a", "rate-1", "A"))
    store.put_once(TenantRecord("org-b", "rate-1", "B"))

    assert store.get("org-a", "rate-1").value == "A"
    assert store.get("org-b", "rate-1").value == "B"
    assert [item.value for item in store.list_for_organization("org-a")] == ["A"]

    try:
        store.put_once(TenantRecord("org-a", "rate-1", "REPLACED"))
    except TenantStorageError as exc:
        assert "immutable" in str(exc).lower()
    else:
        raise AssertionError("immutable overwrite must fail closed")


def test_cross_tenant_lookup_does_not_fall_back_by_record_id():
    store = ImmutableTenantStore[str]()
    store.put_once(TenantRecord("org-a", "invoice-1", "secret-a"))
    try:
        store.get("org-b", "invoice-1")
    except KeyError:
        pass
    else:
        raise AssertionError("cross-tenant lookup must not reuse another tenant record")


def test_blank_identity_fails_closed():
    try:
        TenantRecord("", "x", "value")
    except TenantStorageError:
        pass
    else:
        raise AssertionError("blank organization must be rejected")
