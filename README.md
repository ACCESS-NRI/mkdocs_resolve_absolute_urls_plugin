# MkDocs resolve absolute URLs Plugin

A MkDocs plugin that resolves absolute URLs relative to a configurable root url, with support for multi-version and multi-locale documentation sites.
Currently this only supports websites hosted through [Read the Docs](https://readthedocs.org/).

## Why do I need this
Mkdocs doesn't natively support absolute links ([reference](https://github.com/mkdocs/mkdocs/issues/192)). In addition, when using documentation with multiple versions or locales (for example on ReadtheDocs), absolute URLs like `/docs/guide.html` become problematic. This plugin:

- Automatically prepends the absolute URLs in your Markdown files with the correct root URL
- Falls back to the `READTHEDOCS_CANONICAL_URL` environment variable when no `root_url` is configured
- Supports linking to specific locales or versions using a simple syntax, keeping the current locale/version (if present) when they are not inlcuded in the absolute link

## How it works

### Basic URL resolution

The plugin resolves absolute URLs by prepending a base URL (either from your config or from the Read the Docs environment):

| Absolute URL | Base URL | Result |
|---|---|---|
| `/bar/foo.png` | `https://mywebsite.com` | `https://mywebsite.com/bar/foo.png` |
| `/bar/foo.png` | `https://mywebsite.com/subpage/` | `https://mywebsite.com/subpage/bar/foo.png` |
| `/bar/foo.png` | *(from RTD env)* `https://docs.example.org` | `https://docs.example.org/bar/foo.png` |

### Cross-locale and cross-version links

For multi-version/multi-locale sites, use an extended URL syntax to link to specific versions or locales:

**URL Format:** `/[!<locale>/][@<version>/]<path>`

- `!<locale>` — Switch to a specific locale (optional)
- `@<version>` — Switch to a specific version (optional)
- Omit both to use the current locale/version (if present)

#### Examples

Given base URL `https://mywebsite.com`, current locale `en`, and current version `latest`:

| URL | Resolves to |
|---|---|
| `/my/page` | `https://mywebsite.com/en/latest/my/page` *(current locale & version)* |
| `/!fr/my/page` | `https://mywebsite.com/fr/latest/my/page` *(switch locale)* |
| `/@v2.0/my/page` | `https://mywebsite.com/en/v2.0/my/page` *(switch version)* |
| `/!fr/@v2.0/my/page` | `https://mywebsite.com/fr/v2.0/my/page` *(switch both)* |

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
```

### Configuration options

| Option | Description | Default |
|---|---|---|
| `root_url` | Base URL to prepend to resolved URLs | `READTHEDOCS_CANONICAL_URL` environment variable |
| `attributes` | HTML attributes to process | `["href", "src", "data"]` |
| `prefix` | URL prefix to identify absolute URLs for processing | `/` |

## License

This plugin is licensed under the [CC-BY 4.0 license](https://creativecommons.org/licenses/by/4.0/legalcode).

## Acknowledgements

This project builds on work from [OctoPrint/mkdocs-site-urls](https://github.com/OctoPrint/mkdocs-site-urls). We thank the original authors for their contributions and for publishing their work under an open license.