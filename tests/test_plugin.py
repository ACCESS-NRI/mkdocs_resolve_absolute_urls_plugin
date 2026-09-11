import re
import textwrap

import pytest

from unittest.mock import MagicMock

from mkdocs.commands.build import build
from mkdocs.config import load_config
from mkdocs.exceptions import ConfigurationError
from resolve_absolute_urls.plugin import ResolveAbsoluteUrlsPlugin

@pytest.fixture
def mock_plugin_config():
    return {"attributes": ["src", "href"], "prefix": "/", "base_url": "/docs"}


@pytest.fixture
def create_plugin(mock_plugin_config):
    """Factory function to create the plugin with the prescribed configuration options."""

    def _plugin(config=mock_plugin_config, **kwargs):
        plugin = ResolveAbsoluteUrlsPlugin()
        plugin.load_config(config)
        for key, value in kwargs.items():
            setattr(plugin, key, value)
        return plugin

    return _plugin


@pytest.mark.parametrize(
    "attributes, prefix, string_to_match, match_group1, match_group3, should_match",
    [
        (
            ["href", "src"],
            "/docs/",
            'src = "/docs/image.png"',
            "src",
            "image.png",
            True,
        ),  # valid1
        (
            ["href", "src"],
            "/",
            "href ='/docs/image.png'",
            "href",
            "docs/image.png",
            True,
        ),  # valid2
        (
            ["data"],
            "site:",
            "data=   'site:image.png'",
            "data",
            "image.png",
            True,
        ),  # valid3
        (
            ["href", "src"],
            "/docs/",
            'src = "/image.png"',
            None,
            None,
            False,
        ),  # invalid_different_prefix
        (
            ["href", "src"],
            "/",
            "href ='site:docs/image.png'",
            None,
            None,
            False,
        ),  # invalid_different_prefix2
        (
            ["data"],
            "/",
            "href='/image.png'",
            None,
            None,
            False,
        ),  # invalid_different_attribute
    ],
    ids=[
        "valid1",
        "valid2",
        "valid3",
        "invalid_different_prefix",
        "invalid_different_prefix2",
        "invalid_different_attribute",
    ],
)
def test_on_config_sets_regex(
    create_plugin,
    attributes,
    prefix,
    string_to_match,
    match_group1,
    match_group3,
    should_match,
):
    """Test the on_config method of the ResolveAbsoluteUrlsPlugin."""
    plugin_config = {
        "attributes": attributes,
        "prefix": prefix,
        "base_url": "/docs",
    }
    plugin = create_plugin(plugin_config)
    plugin.on_config(MagicMock())

    # Check that the regex is compiled
    assert isinstance(plugin._regex, re.Pattern)
    match = plugin._regex.search(string_to_match)

    # Check regex is correct
    if should_match:
        assert match is not None
        assert match.group(1) == match_group1
        assert match.group(3) == match_group3
    else:
        assert match is None

@pytest.mark.parametrize(
    "env_version, env_language, link, expected_link",
    [
        (
            None,
            None,
            "/my/absolute/link.png",
            "/docs/my/absolute/link.png",
        ),  # no_version_no_locale
        (
            "v2.0",
            "fr",
            "/my/absolute/link.png",
            "/docs/fr/v2.0/my/absolute/link.png",
        ),  # version_and_locale_from_env
        (
            "v2.0",
            "fr",
            "/!de/my/absolute/link.png",
            "/docs/de/v2.0/my/absolute/link.png",
        ),  # locale_override_only
        (
            "v2.0",
            "fr",
            "/@v3.0/my/absolute/link.png",
            "/docs/fr/v3.0/my/absolute/link.png",
        ),  # version_override_only
        (
            "v2.0",
            "fr",
            "/!de/@v3.0/my/absolute/link.png",
            "/docs/de/v3.0/my/absolute/link.png",
        ),  # locale_and_version_override
        (
            None,
            None,
            "/!de/@v3.0/my/absolute/link.png",
            "/docs/de/v3.0/my/absolute/link.png",
        ),  # override_without_env_vars
    ],
    ids=[
        "no_version_no_locale",
        "version_and_locale_from_env",
        "locale_override_only",
        "version_override_only",
        "locale_and_version_override",
        "override_without_env_vars",
    ],
)
def test_on_post_page(
    create_plugin, monkeypatch, env_version, env_language, link, expected_link
):
    """Test the on_post_page method resolves the current/overridden version and locale."""
    if env_version is None:
        monkeypatch.delenv("READTHEDOCS_VERSION", raising=False)
    else:
        monkeypatch.setenv("READTHEDOCS_VERSION", env_version)
    if env_language is None:
        monkeypatch.delenv("READTHEDOCS_LANGUAGE", raising=False)
    else:
        monkeypatch.setenv("READTHEDOCS_LANGUAGE", env_language)

    plugin = create_plugin({"attributes": ["src"], "prefix": "/", "base_url": "/docs"})
    page = MagicMock()
    config = MagicMock()

    output = f'<img src="{link}" alt="Image">'
    expected_result = f'<img src="{expected_link}" alt="Image">'

    plugin.on_config(config)
    result = plugin.on_post_page(output, page, config)
    assert result == expected_result


def test_on_post_page_url_trailing_slash_is_ignored(create_plugin, monkeypatch):
    """Test that a trailing slash on the `base_url` option does not affect the result."""
    monkeypatch.delenv("READTHEDOCS_VERSION", raising=False)
    monkeypatch.delenv("READTHEDOCS_LANGUAGE", raising=False)

    plugin = create_plugin({"attributes": ["src"], "prefix": "/", "base_url": "/docs/"})
    page = MagicMock()
    config = MagicMock()

    output = '<img src="/image.png">'
    expected_result = '<img src="/docs/image.png">'

    plugin.on_config(config)
    result = plugin.on_post_page(output, page, config)
    assert result == expected_result


def test_on_post_page_unmatched_attributes_are_untouched(create_plugin, monkeypatch):
    """Test that attributes/urls not matching the plugin configuration are left as-is."""
    monkeypatch.delenv("READTHEDOCS_VERSION", raising=False)
    monkeypatch.delenv("READTHEDOCS_LANGUAGE", raising=False)

    plugin = create_plugin({"attributes": ["data"], "prefix": "prefix", "base_url": "/docs"})
    page = MagicMock()
    config = MagicMock()

    output = '''
    <img data="site:docs/image.svg" class="example">
    <img attr  ="prefix/docs/image.png" >
    '''

    plugin.on_config(config)
    result = plugin.on_post_page(output, page, config)
    assert result == output


def test_on_config_falls_back_to_readthedocs_canonical_url(create_plugin, monkeypatch):
    """Test that `base_url` defaults to the READTHEDOCS_CANONICAL_URL env var when not configured."""
    monkeypatch.setenv("READTHEDOCS_CANONICAL_URL", "https://example.com/docs/")
    monkeypatch.delenv("READTHEDOCS_VERSION", raising=False)
    monkeypatch.delenv("READTHEDOCS_LANGUAGE", raising=False)

    plugin = create_plugin({"attributes": ["src"], "prefix": "/"})
    page = MagicMock()
    config = MagicMock()

    output = '<img src="/image.png">'
    expected_result = '<img src="https://example.com/docs/image.png">'

    plugin.on_config(config)
    result = plugin.on_post_page(output, page, config)
    assert result == expected_result


def test_on_config_prefers_explicit_url_over_readthedocs_canonical_url(
    create_plugin, monkeypatch
):
    """Test that an explicitly configured `base_url` takes precedence over the env var."""
    monkeypatch.setenv("READTHEDOCS_CANONICAL_URL", "https://example.com/other/")

    plugin = create_plugin({"attributes": ["src"], "prefix": "/", "base_url": "/docs"})

    plugin.on_config(MagicMock())
    assert plugin._base_url == "/docs"


def test_on_config_raises_when_no_url_is_available(create_plugin, monkeypatch):
    """Test that a ConfigurationError is raised when `base_url` is not configured and the
    READTHEDOCS_CANONICAL_URL env var is not set."""
    monkeypatch.delenv("READTHEDOCS_CANONICAL_URL", raising=False)

    plugin = create_plugin({"attributes": ["src"], "prefix": "/"})

    with pytest.raises(ConfigurationError):
        plugin.on_config(MagicMock())


def test_plugin_real_case(tmp_path, monkeypatch):
    """Run the plugin through an actual `mkdocs build` on a versioned/localized
    Read the Docs build, mixing several attributes, locale/version overrides
    and links that should be left untouched."""
    monkeypatch.setenv("READTHEDOCS_VERSION", "v1.2")
    monkeypatch.setenv("READTHEDOCS_LANGUAGE", "en")

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text(
        textwrap.dedent(
            """\
            # Home

            ![Logo](/images/logo.png)

            [Getting started](/guide/getting-started/)

            [Getting started (French)](/!fr/guide/getting-started/)

            [Migration guide](/@v2.0/guide/migration/)

            [External link](https://example.com/external)

            [Relative link](relative.md)
            """
        )
    )
    (docs_dir / "relative.md").write_text("# Relative page\n")

    mkdocs_yml = tmp_path / "mkdocs.yml"
    mkdocs_yml.write_text(
        textwrap.dedent(
            """\
            site_name: Test site
            docs_dir: docs
            site_dir: site
            plugins:
              - resolve-absolute-urls:
                  attributes: [href, src]
                  prefix: /
                  base_url: /docs
            """
        )
    )

    config = load_config(config_file=str(mkdocs_yml))
    build(config)

    output = (tmp_path / "site" / "index.html").read_text()

    assert 'src="/docs/en/v1.2/images/logo.png"' in output
    assert 'href="/docs/en/v1.2/guide/getting-started/"' in output
    assert 'href="/docs/fr/v1.2/guide/getting-started/"' in output
    assert 'href="/docs/en/v2.0/guide/migration/"' in output
    assert 'href="https://example.com/external"' in output
    assert 'href="relative/"' in output