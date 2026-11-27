# Security

## Reporting a vulnerability

Use **Report a vulnerability** on this repository's Security tab, never a public issue. It covers the server's code, the image `ghcr.io/marceltov/karakeep-mcp` and the dependencies it ships. You get an answer within seven days. The advisory is published with your name, unless you'd rather not be named.

Never post an API key, a password or bookmarks of a real account, also not in a private report: describe the shape instead.

## Supported versions

Only the newest release gets fixes; there are no backports.

## What each release carries

- The image `ghcr.io/marceltov/karakeep-mcp:X.Y.Z` with its SBOM and build provenance attached (`docker buildx imagetools inspect ghcr.io/marceltov/karakeep-mcp:X.Y.Z --format '{{ json .SBOM }}'`, `gh attestation verify oci://ghcr.io/marceltov/karakeep-mcp:X.Y.Z --repo marceltov/karakeep-mcp`).
- `karakeep-mcp-vX.Y.Z.cdx.json` on the GitHub release: a CycloneDX SBOM of the image.

## How this repository watches

- Private vulnerability reporting and secret scanning with push protection (also over the tests).
- CodeQL through the shared workflow of Marceltov/engineering-conventions (`.github/workflows/codeql.yml` calls it), on every pull request, every push to `main` and weekly. It leaves out the tests.
- Dependabot alerts and pull requests for the Python dependencies, the base image and GitHub Actions; patch and minor bumps merge by themselves once CI is green.
- A daily `pip-audit` of the runtime dependencies and a scan of the published image (`.github/workflows/audit.yml`).
