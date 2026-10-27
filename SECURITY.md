# Security Policy

InvestIQ is experimental software and is not approved to store credentials or manage real-money orders. Connected CLI calls obtain an individual API key from the `TWELVE_DATA_API_KEY` environment variable; snapshots **never** store this key or the quote entitlement scope. Users must secure shell history, environment variables, exported research text and local directories.

## Reporting
Please do not publish exploitable vulnerabilities in public issues. Use GitHub's **Report a vulnerability** / private security advisory feature if enabled; otherwise contact the maintainers privately via their published GitHub profile before disclosure.

Never commit API tokens, brokerage credentials, financial account details, personal datasets, or commercially restricted data. Use environment variables for optional local integrations; `.env` files are ignored.

At this stage there is no guaranteed vulnerability response SLA. Supported release branches will be documented once stable versions are released.


## v0.3 local Research Desk and private history (personal alpha)

The local app listens on IPv4 loopback only and checks Host, Origin, same-origin
session cookies and anti-CSRF tokens. **Localhost is not a same-OS-user
authorization boundary:** other software/users on the computer can connect to
the loopback port. When the app is started with `--research-dir`, it now
generates a random **per-launch private-history access code**, printed only
to the launch terminal. The browser requires that code before listing,
opening, exporting or saving history, even if it already has its own valid
session/CSRF token. Unlock state is specific to one cookie session and revoked
on disconnect/expiry/server restart. The code is never placed in HTTP session
responses, URLs, persistent settings, log files or Git. Keep the terminal
private. This is an additional capability gate, **not** protection from
malware, process-memory inspection, compromised OS users or all local attacks.

The browser form submits provider/model API keys directly to the loopback
server. These secrets are process-memory-only; never paste a key into the
research question, note fields or exported files. This tool is not safe to
expose via a reverse proxy, remote port forwarding, a shared kiosk, or a
public/office network. A restrictive private directory and OS full-disk
encryption/backups remain necessary; the app does not encrypt files or securely
erase deleted data. If the code is exposed, stop and restart the server to
rotate it. Browser research/model execution and SEC/quote provider terms require
independent authorization.

There has been no independent penetration test or cross-OS security
certification. Do not infer production readiness from offline acceptance tests.
