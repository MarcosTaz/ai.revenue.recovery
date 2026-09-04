# AERVIND Email Operations

Status: configuration in progress (custom domain claimed in Primitive; DNS verification pending).

## Canonical mail architecture

- Domain / DNS registrar: Porkbun (`aervind.com`)
- Mail infrastructure: Primitive Email, Developer tier
- Primary human sender: `marcos@aervind.com`
- General inbound: `hello@aervind.com`
- Partner / referral inbound: `partners@aervind.com`
- Finance / invoice inbound: `billing@aervind.com`

Do not create fake departmental mailboxes. AERVIND should present one accountable human identity for commercial conversations and use functional addresses only where they correspond to a real workflow.

## Operating model

Primitive custom domains are address/route based rather than separate paid mailboxes. Once the domain is verified, inbound messages can be stored and read through the connected Primitive tooling and outbound mail can be sent from addresses on the verified domain subject to Primitive recipient gates and acceptable-use rules.

Assistant workflow:

1. detect/read new inbound mail;
2. recover the full thread;
3. classify sender, account, request, urgency and risk;
4. draft the recommended response in AERVIND's aviation-advisory tone;
5. surface material decisions to Marcos;
6. send only when sending is explicitly authorized;
7. preserve threading and inspect delivery status;
8. continue follow-up until the commercial thread is resolved.

An hourly condition watch is configured to surface only new/material AERVIND inbound messages and prepare a recommended reply. It must not send autonomously without explicit authorization.

## Commercial sending rule

The primary branded domain is not a bulk-cold-email domain. Do not use it for unsolicited bulk/commercial blasts or high-volume sequence automation. First-touch acquisition should remain selective, account-specific and compliant with the sending platform and applicable law. Once a recipient has engaged, the ongoing relationship moves to `marcos@aervind.com`.

## DNS records required by Primitive

Publish these records in Porkbun and then re-run Primitive domain verification.

```dns
@ 3600 IN MX 10 mx1.primitive.dev.
_primitive 3600 IN TXT "primitive-verify=8606a9d744c2623cf05a3fd3d6e763e3d32dc6743e24622e"
@ 3600 IN TXT "v=spf1 include:_spf.primitive.dev ~all"
pri-a35cf8._domainkey 3600 IN TXT "v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwSIG7SzFQhngk6zBVkzIrkhW87Tka4vxAdURYPK5snF0ziGcVbXVVdmYoUt7bPGKIzAYFOM9bjSuXqXLDVqrkoxzNAhetOtTvOdcxvG0Nj3Ul5czrbJqgh2Zqug4uXL5UScvsYEqE5hggjJTHgUlxdooCnplPCCPFHv8WHsuHcTnxfGjDupmQ3gAOOkR73xUwrz+JPklQC9eeXhRTX8HhwNdK9PEAcEfDxd87bqn7YQVQlsNP+zC4MAqbxcW4sbTDqPcyzeBcpsWmxyldybypoD9pEymRHpJPfiwBgPY28hk6PGVgk30HHL2507alYdYrpMCnRkOHrwob5deyWVdowIDAQAB"
_dmarc 3600 IN TXT "v=DMARC1; p=none; rua=mailto:dmarc@aervind.com"
_smtp._tls 3600 IN TXT "v=TLSRPTv1; rua=mailto:tlsrpt@aervind.com"
```

Porkbun root host is blank (rather than `@`) when its UI requests a Host value. Keep unrelated website A/AAAA/ALIAS/CNAME records. Remove/replace conflicting root MX records and ensure there is only one root SPF TXT record.

## Verification gate

Do not claim branded email is live until all of the following pass:

- ownership TXT
- MX
- SPF
- DKIM
- DMARC
- TLS-RPT
- inbound test to `marcos@aervind.com`
- reply test preserving thread
- outbound delivery test from `marcos@aervind.com`

No private credentials, API keys, tax identifiers or banking data belong in this repository.
