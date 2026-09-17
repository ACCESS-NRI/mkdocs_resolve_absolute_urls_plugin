import logging
import re
from unittest.mock import MagicMock

import pytest

from mkdocs.exceptions import ConfigurationError
from resolve_absolute_urls.plugin import (
    ResolveAbsoluteUrlsPlugin,
    logger,
    replace_locale,
    replace_version,
)


@pytest.fixture
def default_plugin_config():
    return {
        "attributes": None, 
        "prefix": None, 
        "root_url": None,
        "url_versioning_scheme": None,
    }


@pytest.fixture
def create_plugin(default_plugin_config,monkeypatch):
    """Factory function to create the plugin with the prescribed configuration options."""

    def _plugin(
        config=default_plugin_config, 
        command="build"
    ):
        plugin = ResolveAbsoluteUrlsPlugin()
        plugin.on_startup(command=command, dirty=False)
        plugin.load_config(config)
        return plugin

    return _plugin


def test_replace_locale():
    assert replace_locale("/my/example/en/v1.0", "locale") == "/my/example/locale/v1.0"

def test_replace_version():
    assert replace_version("/my/example/en/v1.0", "v1") == "/my/example/en/v1"

@pytest.mark.parametrize(
    "command",
    ["build", "serve"],
    ids=["build", "serve"]
)
@pytest.mark.parametrize(
    "root_url_config, url_env_var",
    [
        ("https://example.com/it/v1.0", None),
        (None, "https://example.com/it/v1.0"),
    ],
    ids=[
        "root_url_config",
        "root_url_env",
    ]
)
@pytest.mark.parametrize(
    "attributes, prefix, string_to_match, match_attribute, match_remainder, should_match",
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
def test_regex(
    create_plugin, monkeypatch, command, attributes, prefix, root_url_config, url_env_var,
    string_to_match, match_attribute, match_remainder, should_match,
):
    """Test the regex int the on_config method of the ResolveAbsoluteUrlsPlugin."""

    plugin_config = {
        "attributes": attributes,
        "prefix": prefix,
        "root_url": "/docs",
    }
    plugin = create_plugin(plugin_config, command=command)

    if command == "build":
        assert plugin.is_serving is False
    else:
        assert plugin.is_serving is True

    plugin.on_config(MagicMock())

    # Check that the regex is compiled
    assert isinstance(plugin.url_regex, re.Pattern)
    
    # Check regex is correct
    match = plugin.url_regex.search(string_to_match)
    if should_match:
        assert match is not None
        assert match.group("attribute") == match_attribute
        assert match.group("remainder") == match_remainder
    else:
        assert match is None


@pytest.mark.parametrize(
    "command",
    ["build", "serve"],
    ids=["build", "serve"]
)
def test_no_root_url_no_env(create_plugin, default_plugin_config, monkeypatch, command):
    """Test the plugin behavior when no root URL and no environment variables are set."""
    monkeypatch.delenv("READTHEDOCS_CANONICAL_URL", raising=False)
    plugin = create_plugin(default_plugin_config, command=command)
    if command == "build":
        assert plugin.is_serving is False
        with pytest.raises(ConfigurationError):
            plugin.on_config(MagicMock())
    else:
        assert plugin.is_serving is True
        plugin.on_config(MagicMock())
        # Check that the absolute links remain unchanged when serving
        result = plugin.on_post_page('<img src="/my/abs/link" alt="Image">', MagicMock(), MagicMock())
        assert result == '<img src="/my/abs/link" alt="Image">'


def test_url_root_precedence_over_env(create_plugin, monkeypatch):
    """Test the plugin behavior when a root URL is set and environment variables are present."""
    monkeypatch.setenv("READTHEDOCS_CANONICAL_URL", "www.myexamplesitefromenv.com/")
    plugin = create_plugin({"root_url": "www.myexamplesitefromroot_url.com/"})
    plugin.on_config(MagicMock())
    
    html_input = '<img src="/my/abs/link" alt="Image">'
    expected_result = '<img src="www.myexamplesitefromroot_url.com/my/abs/link" alt="Image">'

    result = plugin.on_post_page(html_input, MagicMock(), MagicMock())
    assert result == expected_result


@pytest.mark.parametrize(
    "command",
    ["build","serve"],
    ids=["build","serve"]
)
@pytest.mark.parametrize(
    "root_url_config, url_env_var",
    [
        ("https://example.com/it/v1.0", None),
        (None, "https://example.com/it/v1.0"),
    ],
    ids=[
        "root_url_config",
        "root_url_env",
    ]
)
@pytest.mark.parametrize(
    "absolute_url, expected_resolved_url, warn",
    [
        (
            "/my/absolute/link.png",
            "https://example.com/it/v1.0/my/absolute/link.png",
            False,
        ),  # no_overrides
        (
            "/!de/my/absolute/link.png",
            "https://example.com/de/v1.0/my/absolute/link.png",
            False,
        ),  # locale_override
        (
            "/@v3.0/my/absolute/link.png",
            "https://example.com/it/v3.0/my/absolute/link.png",
            False,
        ),  # version_override
        (
            "/!de/@v3.0/my/absolute/link.png",
            "https://example.com/de/v3.0/my/absolute/link.png",
            False,
        ),  # locale_and_version_override
    ],
    ids=[
        "no_overrides",
        "locale_override",
        "version_override",
        "locale_and_version_override",
    ],
)
def test_resolve_absolute_urls_with_overrides_url_scheme_multiple_versions_with_translations(
    create_plugin, default_plugin_config, root_url_config, monkeypatch,
    url_env_var, absolute_url, expected_resolved_url, warn, caplog, command
):
    """
    Test that the plugin resolves the absolute URLs correctly even with locale
    or version overrides, for URL versioning scheme "multiple_versions_with_translations",
    for root_url set either via the plugin configuration or the environment variable.
    """
    serve_expected_url = "/my/absolute/link.png"
    url_versioning_scheme = "multiple_versions_with_translations"
    plugin_config = {
        "root_url": root_url_config,
        "url_versioning_scheme": url_versioning_scheme
    }
    if url_env_var:
        monkeypatch.setenv("READTHEDOCS_CANONICAL_URL", url_env_var)
    else:
        monkeypatch.delenv("READTHEDOCS_CANONICAL_URL", raising=False)
    html_input = f'<img src="{absolute_url}" alt="Image">'
    expected_result = f'<img src="{expected_resolved_url if command == "build" else serve_expected_url}" alt="Image">'

    plugin = create_plugin(plugin_config, command=command)
    if command == "build":
        assert plugin.is_serving is False
    else:
        assert plugin.is_serving is True
    plugin.on_config(plugin_config)
    with caplog.at_level(logging.WARNING, logger=logger.name):
        result = plugin.on_post_page(html_input, MagicMock(), MagicMock())
    assert result == expected_result
    if warn and command == "build":
        assert "Make sure the resulting resolved URL is correct!" in caplog.text
    else:
        assert caplog.text == ""


@pytest.mark.parametrize(
    "command",
    ["build", "serve"],
    ids=["build", "serve"]
)
@pytest.mark.parametrize(
    "root_url_config, url_env_var",
    [
        ("https://example.com/v1.0", None),
        (None, "https://example.com/v1.0"),
    ],
    ids=[
        "root_url_config",
        "root_url_env",
    ]
)
@pytest.mark.parametrize(
    "absolute_url, expected_resolved_url, warn",
    [
        (
            "/my/absolute/link.png",
            "https://example.com/v1.0/my/absolute/link.png",
            False,
        ),  # no_overrides
        (
            "/!de/my/absolute/link.png",
            "https://example.com/v1.0/my/absolute/link.png",
            True,
        ),  # locale_override
        (
            "/@v3.0/my/absolute/link.png",
            "https://example.com/v3.0/my/absolute/link.png",
            False,
        ),  # version_override
        (
            "/!de/@v3.0/my/absolute/link.png",
            "https://example.com/v3.0/my/absolute/link.png",
            True,
        ),  # locale_and_version_override
    ],
    ids=[
        "no_overrides",
        "locale_override",
        "version_override",
        "locale_and_version_override",
    ],
)
def test_resolve_absolute_urls_with_overrides_url_scheme_multiple_versions_without_translations(
    create_plugin, default_plugin_config, root_url_config, monkeypatch,
    url_env_var, absolute_url, expected_resolved_url, warn, caplog, command
):
    """
    Test that the plugin resolves the absolute URLs correctly even with locale
    or version overrides, for URL versioning scheme "multiple_versions_with_translations",
    for root_url set either via the plugin configuration or the environment variable.
    """
    serve_expected_url = "/my/absolute/link.png"
    url_versioning_scheme = "multiple_versions_without_translations"
    plugin_config = {
        "root_url": root_url_config,
        "url_versioning_scheme": url_versioning_scheme
    }
    if url_env_var:
        monkeypatch.setenv("READTHEDOCS_CANONICAL_URL", url_env_var)
    else:
        monkeypatch.delenv("READTHEDOCS_CANONICAL_URL", raising=False)
    html_input = f'<img src="{absolute_url}" alt="Image">'
    expected_result = f'<img src="{expected_resolved_url if command == "build" else serve_expected_url}" alt="Image">'
    plugin = create_plugin(plugin_config, command=command)
    if command == "build":
        assert plugin.is_serving is False
    else:
        assert plugin.is_serving is True
    plugin.on_config(plugin_config)
    with caplog.at_level(logging.WARNING, logger=logger.name):
        result = plugin.on_post_page(html_input, MagicMock(), MagicMock())
    assert result == expected_result
    if warn and command == "build":
        assert "Make sure the resulting resolved URL is correct!" in caplog.text
    else:
        assert caplog.text == ""


@pytest.mark.parametrize(
    "command",
    ["build", "serve"],
    ids=["build", "serve"]
)
@pytest.mark.parametrize(
    "root_url_config, url_env_var",
    [
        ("https://example.com/", None),
        (None, "https://example.com/"),
    ],
    ids=[
        "root_url_config",
        "root_url_env",
    ]
)
@pytest.mark.parametrize(
    "absolute_url, expected_resolved_url, warn",
    [
        (
            "/my/absolute/link.png",
            "https://example.com/my/absolute/link.png",
            False,
        ),  # no_overrides
        (
            "/!de/my/absolute/link.png",
            "https://example.com/my/absolute/link.png",
            True,
        ),  # locale_override
        (
            "/@v3.0/my/absolute/link.png",
            "https://example.com/my/absolute/link.png",
            True,
        ),  # version_override
        (
            "/!de/@v3.0/my/absolute/link.png",
            "https://example.com/my/absolute/link.png",
            True,
        ),  # locale_and_version_override
    ],
    ids=[
        "no_overrides",
        "locale_override",
        "version_override",
        "locale_and_version_override",
    ],
)
def test_resolve_absolute_urls_with_overrides_url_scheme_single_version_without_translations(
    create_plugin, default_plugin_config, root_url_config, monkeypatch,
    url_env_var, absolute_url, expected_resolved_url, warn, caplog, command
):
    """
    Test that the plugin resolves the absolute URLs correctly even with locale
    or version overrides, for URL versioning scheme "single_version_without_translations",
    for root_url set either via the plugin configuration or the environment variable.
    """
    serve_expected_url = "/my/absolute/link.png"
    url_versioning_scheme = "single_version_without_translations"
    plugin_config = {
        "root_url": root_url_config,
        "url_versioning_scheme": url_versioning_scheme
    }
    if url_env_var:
        monkeypatch.setenv("READTHEDOCS_CANONICAL_URL", url_env_var)
    else:
        monkeypatch.delenv("READTHEDOCS_CANONICAL_URL", raising=False)
    html_input = f'<img src="{absolute_url}" alt="Image">'
    expected_result = f'<img src="{expected_resolved_url if command == "build" else serve_expected_url}" alt="Image">'
    
    plugin = create_plugin(plugin_config, command=command)
    if command == "build":
        assert plugin.is_serving is False
    else:
        assert plugin.is_serving is True
    plugin.on_config(plugin_config)
    with caplog.at_level(logging.WARNING, logger=logger.name):
        result = plugin.on_post_page(html_input, MagicMock(), MagicMock())
    assert result == expected_result
    if warn and command == "build":
        assert "Make sure the resulting resolved URL is correct!" in caplog.text
    else:
        assert caplog.text == ""


@pytest.mark.parametrize(
    "root_url_config, url_env_var",
    [
        ("https://example.com/", None),
        (None, "https://example.com/"),
    ],
    ids=[
        "root_url_config",
        "root_url_env",
    ]
)
def test_unmatched_attributes_are_untouched(
    create_plugin, default_plugin_config, monkeypatch,
    root_url_config, url_env_var
):
    """Test that urls not matching are left as-is."""
    plugin_config = {
        "root_url": root_url_config,
        "attributes": ["src"],
        "prefix": "prefix/",
    }
    if url_env_var:
        monkeypatch.setenv("READTHEDOCS_CANONICAL_URL", url_env_var)
    else:
        monkeypatch.delenv("READTHEDOCS_CANONICAL_URL", raising=False)
    html_input = '''
    <img data="site:docs/image.svg" class="example">
    <img src="prefix/docs/image.png" >
    <img data="prefix/docs/image.png" >
    '''
    expected_result = '''
    <img data="site:docs/image.svg" class="example">
    <img src="https://example.com/docs/image.png" >
    <img data="prefix/docs/image.png" >
    '''
    
    plugin = create_plugin(plugin_config)
    plugin.on_config(plugin_config)
    result = plugin.on_post_page(html_input, MagicMock(), MagicMock())
    assert result == expected_result