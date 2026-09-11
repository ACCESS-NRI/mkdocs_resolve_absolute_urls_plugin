# MkDocs resolve absolute URLs Plugin

## About
A MkDocs plugin to resolve absolute URLs relative to a configured `url`, rather than the root url of the website.

For example:

| absolute URL | url | resulting URL |
| --- | -------- | ------------- |
| `/images/foo.png` | `/` | `/images/foo.png` |
| `/images/foo.png` | `/subpage/` | `/subpage/images/foo.png` |

### Locales and versions
If the site is built with multiple versions/locales (e.g. via [Read the Docs](https://readthedocs.org/)), the current version and locale are read from the `READTHEDOCS_VERSION` and `READTHEDOCS_LANGUAGE` environment variables and appended to `url` (which should not itself contain a version/locale), before the rest of the link.

You can also link to a specific locale and/or version, instead of the current one, by prefixing the absolute link with `!locale` and/or `@version`, e.g.:

| absolute URL | resulting link (relative to `url`) |
| --- | --- |
| `/my/page` | current locale/version, e.g. `/en/latest/my/page` |
| `/!fr/my/page` | `fr` locale, current version, e.g. `/fr/latest/my/page` |
| `/@v2.0/my/page` | current locale, `v2.0` version, e.g. `/en/v2.0/my/page` |
| `/!fr/@v2.0/my/page` | `fr` locale, `v2.0` version, e.g. `/fr/v2.0/my/page` |

## Configuration

| Name | Description | Default value |
| ---------------- | ----------- | -------- |
| `attributes` | The HTML attributes whose absolute URLs will be resolved. | `["href", "src", "data"]` |
| `prefix` | Prefix used to denote the absolute URLs. If the URLs starts with this `prefix`, it will be resolved.| `/` |
| `url` | The url to prepend to the resolved absolute URLs. If not set, it defaults to the [Read the Docs](https://readthedocs.org/) `READTHEDOCS_CANONICAL_URL` environment variable. | |

## Example usage

```yaml
plugins:
  - resolve-absolute-urls:
      attributes:
        - href
        - data-url
      prefix: /
      url: /docs/
```

## License
The ACCESS-Hive Docs website is covered by the [CC-BY 4.0 license](https://creativecommons.org/licenses/by/4.0/legalcode).

However, the material linked to from ACCESS-Hive Docs is covered by various licensing agreements. Our users should directly refer to the terms and conditions of any material they are using to understand their rights and responsibilities.

## Ackowledgements
This project is based on work from [OctoPrint/mkdocs-site-urls](https://github.com/OctoPrint/mkdocs-site-urls).  
We thank the original authors for their contributions and for making their work available under an open license.