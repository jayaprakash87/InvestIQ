# Security Policy

InvestIQ is experimental software and is not approved to store credentials or manage real-money orders. Connected CLI calls obtain an individual API key from the `TWELVE_DATA_API_KEY` environment variable; snapshots **never** store this key or the quote entitlement scope. Users must secure shell history, environment variables, exported research text and local directories.

## Reporting
Please do not publish exploitable vulnerabilities in public issues. Use GitHub's **Report a vulnerability** / private security advisory feature if enabled; otherwise contact the maintainers privately via their published GitHub profile before disclosure.

Never commit API tokens, brokerage credentials, financial account details, personal datasets, or commercially restricted data. Use environment variables for optional local integrations; `.env` files are ignored.

At this stage there is no guaranteed vulnerability response SLA. Supported release branches will be documented once stable versions are released.
