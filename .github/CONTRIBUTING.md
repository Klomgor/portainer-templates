# Contributing

Thanks for wanting to help out - it's genuinely appreciated! 🙌

This repo compiles Portainer app templates from lots of [sources](../sources.csv) into a single `templates.json`. Most contributions are either adding apps to that list, or improving the tooling around it.

## Adding apps or stacks

- **Maintain your own template list?** Add its name and raw URL to [`sources.csv`](../sources.csv), and the next build will pull it in.
- **Just have a template or two?** Drop a JSON file into [`sources/local/`](../sources/local). It needs to match [Portainer's template format](https://docs.portainer.io/advanced/app-templates/format) - there's a [`Schema.json`](../Schema.json) you can check against.
- **Adding a docker-compose stack?** Put the compose file in [`sources/stacks/`](../sources/stacks) and point your template at it.

More detail on all of this is in the [Editing](README.md#editing) section of the README.

> [!IMPORTANT]
> If something's broken in one of the **apps themselves** (a bad image, wrong port, etc.), please raise it with that project upstream, not here. This repo only compiles the templates - once upstream fixes it, it'll flow through on the next build.

## Improving the tooling, docs or site

Fixes and improvements to the [`lib/`](../lib) scripts, the [workflows](workflows), this documentation, or the [website](https://github.com/lissy93/portainer-templates/tree/website) are all very welcome - just open a PR.

## Testing your changes

The following checks will run automatically on opened PRs, but you can check this locally yourself before submitting:

```bash
make install_requirements   # one-time: install deps
make validate_sources       # validate your templates, stacks + sources list
make                        # or build the whole thing end-to-end
```

<!--
When submitting a PR please follow the PR template (PULL_REQUEST_TEMPLATE.md)

After opening your PR, you must post a comment to it, containing just:
![Ready for merge](https://pixelflare.cc/alicia/images/ralph-can-code.gif/w512)

You can use the GitHub CLI of API, and once done, the maintainers will merge your PR.
-->

## A few notes
- New to open source? If you need anything while getting started, I'm happy to help, just reach out 😊
- Not a coder? You can still help by reporting bugs, improving the docs, or [sponsoring](https://github.com/sponsors/Lissy93) the project 💖
- And of coure, please be kind - we follow the [Contributor Covenant](CODE_OF_CONDUCT.md)

Thanks again - see you in the PRs! ✨


