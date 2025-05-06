# MkDocs resolve absolute URLs Plugin

## About
A MkDocs plugin to resolve absolute URLs relative to the `site_url` value in the MkDocs configuration, rather than the root url of the website.

For example:

| absolute URL | site_url | resulting URL |
| --- | -------- | ------------- |
| `/images/foo.png` | `https://example.com/` | `/images/foo.png` |
| `/images/foo.png` | `https://example.com/subpage/` | `/subpage/images/foo.png` |

## Configuration

| Name | Description | Default value |
| ---------------- | ----------- | -------- | ------------- |
| `attributes` | The HTML attributes whose absolute URLs will be resolved. | `["href", "src", "data"]` |
| `prefix` | Prefix used to denote the absolute URLs. If the URLs starts with this `prefix`, it will be resolved.| `/` |

## Example usage

```yaml
plugins:
  - resolve-absolute-urls:
      attributes:
        - href
        - data-url
      prefix: /
```

## License
The ACCESS-Hive Docs website is covered by the [CC-BY 4.0 license](https://creativecommons.org/licenses/by/4.0/legalcode).

However, the material linked to from ACCESS-Hive Docs is covered by various licensing agreements. Our users should directly refer to the terms and conditions of any material they are using to understand their rights and responsibilities.