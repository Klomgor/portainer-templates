# Security Policy

Portainer Templates is a compiled list of community app templates, plus a little Python tooling and an NGINX image to build and serve it.
This policy only covers that tooling, the website and the combined `templates.json` - see the note below on the third-party apps themselves.

## Supported Versions
Only the latest minor version is maintained. So please make sure you're using a version from within the last month before reporting.

## Reporting a security issue

If you think you've found a security problem, please securely reach-out, either:
- Open a [security advisory](https://github.com/lissy93/portainer-templates/security/advisories/new) here on GitHub
- Or email me at `security@as93.net` (PGP: [`E10EE533A8E5D6F6E231BBCD4C8DEAFFCE3B8D03`](https://keys.openpgp.org/vks/v1/by-fingerprint/E10EE533A8E5D6F6E231BBCD4C8DEAFFCE3B8D03))

> [!IMPORTANT]
> Please do not report active security issues via public means, without first giving us 30 days to fix it.

## A note on the templates

The templates are gathered from lots of community [sources](../sources.csv) and point at third-party Docker images that I don't maintain or audit. A vulnerability *in one of those apps* is best raised with its upstream project. But if a template in this list looks malicious, points at a dodgy image, or ships an unsafe default, please do tell me and I'll pull it.
