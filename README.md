# MkDocs resolve absolute URLs Plugin

A MkDocs plugin that resolves absolute URLs relative to a configurable root url, with support for multi-version and multi-locale documentation sites based on the configurable url versioning scheme.
Currently this only supports websites hosted through [Read the Docs](https://readthedocs.org/).

## Overview
- [Why do I need this](#why-do-i-need-this)
- [How it works](#how-it-works)
  - [Basic URL resolution](#basic-url-resolution)
  - [Cross-locale and cross-version urls](#cross-locale-and-cross-version-urls)
    - [Examples](#examples)
- [Configuration options](#configuration-options)
- [Usage examples](#usage-examples)
  - [Basic setup](#basic-setup)
  - [With custom settings](#with-custom-settings)
- [License](#license)
- [Acknowledgements](#acknowledgements)


## Why do I need this
Mkdocs doesn't natively support absolute links ([reference](https://github.com/mkdocs/mkdocs/issues/192)). In addition, when using documentation with multiple versions or locales (for example on ReadtheDocs), absolute URLs like `/docs/guide.html` become problematic. This plugin:

- Automatically prepends the absolute URLs in your Markdown files with the correct root URL
- Falls back to the `READTHEDOCS_CANONICAL_URL` environment variable when no `root_url` is configured
- Supports linking to specific locales or versions using a simple syntax, keeping the current locale/version (if present) when they are not inlcuded in the absolute link

## How it works

### Basic URL resolution

The plugin resolves absolute URLs by prepending a root URL (either from your config or from the Read the Docs environment):

| Absolute URL | Root URL | Result |
|---|---|---|
| `/bar/foo.png` | `https://mywebsite.com` | `https://mywebsite.com/bar/foo.png` |
| `/bar/foo.png` | `https://mywebsite.com/subpage/` | `https://mywebsite.com/subpage/bar/foo.png` |

If the root URL is not configured, it is taken from the `READTHEDOCS_CANONICAL_URL` environment variable.

### Cross-locale and cross-version urls

For sites that enable multiple locales and/or multiple versions, you can add the `url_versioning_scheme` option and use an extended URL syntax to link to specific versions or locales:

**URL Format:** `/!<locale>/@<version>/<link>`

- `!<locale>`: Optional locale override to switch to a specific locale. Must be used with `url_versioning_scheme` set to `multiple_versions_with_translations`
- `@<version>`: Optional version override to switch to a specific version. Must be used with `url_versioning_scheme` set to either `multiple_versions_with_translations` or `multiple_versions_without_translations`
- Omit both to use the current locale/version (if present)

#### Examples

Given a root URL `https://mywebsite.com`, url versioning scheme `multiple_versions_with_translations`, current locale `en`, and current version `latest`:

| URL | Resolves to |
|---|---|
| `/my/page` | `https://mywebsite.com/en/latest/my/page` *(current locale & version)* |
| `/!fr/my/page` | `https://mywebsite.com/fr/latest/my/page` *(locale override)* |
| `/@v2.0/my/page` | `https://mywebsite.com/en/v2.0/my/page` *(version override)* |
| `/!fr/@v2.0/my/page` | `https://mywebsite.com/fr/v2.0/my/page` *(locale and version override)* |

## Configuration options

| Option | Description | Default |
|---|---|---|
| `root_url` | Root URL to prepend resolved URLs to | `READTHEDOCS_CANONICAL_URL` environment variable |
| `attributes` | HTML attributes containing the URLs to process | `["href", "src", "data"]` |
| `prefix` | URL prefix to identify absolute URLs for processing | `/` |


## Usage examples

### Basic setup

```yaml
plugins:
  - resolve-absolute-urls
```

### With custom settings

```yaml
plugins:
  - resolve-absolute-urls:
      root_url: https://mywebsite.io/
      attributes:
        - href
        - data-url
      prefix: /abs/
      url_versioning_scheme: multiple_versions_without_translations
```

## License

This plugin is licensed under the [CC-BY 4.0 license](https://creativecommons.org/licenses/by/4.0/legalcode).

## Acknowledgements

This project builds on work from [OctoPrint/mkdocs-site-urls](https://github.com/OctoPrint/mkdocs-site-urls). We thank the original authors for their contributions and for publishing their work under an open license.