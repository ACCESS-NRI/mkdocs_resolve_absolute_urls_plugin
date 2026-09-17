import os
import re
from enum import Enum

import mkdocs.plugins
from mkdocs.config import config_options as c
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.exceptions import ConfigurationError

logger = mkdocs.plugins.get_plugin_logger(__name__)

class UrlVersioningScheme(Enum):
    """
    URL versioning schemes for the plugin configuration.
    The values correspond to the different URL versioning schemes
    supported by ReadTheDocs.
    """
    LOCALE_AND_VERSION = "multiple_versions_with_translations"
    VERSION_ONLY = "multiple_versions_without_translations"
    NONE = "single_version_without_translations"

class Config(mkdocs.config.base.Config):
    root_url = c.Type(str, default="")
    url_versioning_scheme = c.Choice(
        [e.value for e in UrlVersioningScheme],
        default=UrlVersioningScheme.NONE.value,
    )
    attributes = c.Type(list, default=["href", "src", "data"])
    prefix = c.Type(str, default="/")

def replace_locale(url, locale):
    '''
    Replace the locale segment in the given URL of format 
    `.../locale/version` with the specified locale.

    Args:
        url (str): The original URL.
        locale (str): The locale to replace in the URL.

    Returns:
        str: The URL with the locale replaced.
    '''
    parts = url.split("/")
    parts[-2] = locale
    return "/".join(parts)

def replace_version(url, version):
    '''
    Replace the version segment in the given URL of format 
    `.../locale/version` with the specified version.

    Args:
        url (str): The original URL.
        version (str): The version to replace in the URL.

    Returns:
        str: The URL with the version replaced.
    '''
    parts = url.split("/")
    parts[-1] = version
    return "/".join(parts)

class ResolveAbsoluteUrlsPlugin(mkdocs.plugins.BasePlugin[Config]):
    # Matches an optional `!locale` and/or `@version` override at the start of an absolute url, 
    # e.g. `!fr/@v2.0/my/page` -> locale="fr", version="v2.0", link="my/page"
    _OVERRIDE_RE = re.compile(
        r"^(?:!(?P<locale>[^/]+)/)?(?:@(?P<version>[^/]+)/)?(?P<link>.*)$", re.DOTALL
    )

    def on_startup(self, *, command, dirty):
        if command == 'serve':
            self.is_serving = True
        else:
            self.is_serving = False

    def on_config(self, config: MkDocsConfig) -> MkDocsConfig:
        # Define url regex
        attributes = (re.escape(attr) for attr in self.config["attributes"])
        self.prefix = re.escape(self.config["prefix"])
        regex_parts = [
            r"(?P<attribute>", # capturing group for the attribute
            "|".join(attributes), # attributes
            r")", # end capturing group for the attribute
            r"\s*=\s*", # equals sign with optional whitespace
            r"(?P<quote>[\"'])", # capturing group for the quote
            self.prefix, # url prefix
            r"(?P<remainder>[^\"']*)", # capturing group for the absolute url remainder
            r"(?P=quote)", # matching quote
        ]
        url_regex = "".join(regex_parts)
        self.url_regex = re.compile(url_regex, re.IGNORECASE)
        # root URL
        if not self.is_serving:
            root_url = self.config["root_url"]
            # If root_url is not set, get it from the READTHEDOCS_CANONICAL_URL env variable
            if not root_url:
                root_url = os.environ.get("READTHEDOCS_CANONICAL_URL", "")
                if not root_url:
                    raise ConfigurationError(
                        "The 'resolve-absolute-urls' plugin requires a 'root_url' to be configured, "
                        "or the 'READTHEDOCS_CANONICAL_URL' environment variable to be set and non-empty."
                    )
        else:
            root_url = ""
        self._root_url = root_url.rstrip("/")
        self._url_versioning_scheme = UrlVersioningScheme(self.config["url_versioning_scheme"])
        return config

    def on_post_page(self, output, page, config):
        def _replacer(match):
            """
            Replacer function for the URL regex.

            This function is called for each match of the URL regex in the HTML output.
            It extracts the attribute, quote, and remainder of the URL, applies any locale
            or version overrides, and constructs the resolved absolute URL.
            """
            attribute = match.group("attribute")
            remainder = match.group("remainder")
            override = self._OVERRIDE_RE.match(remainder)
            locale_override = override.group("locale")
            version_override = override.group("version")
            link = override.group("link")

            absolute_url = f"{self.prefix}{remainder}"
            root_url = self._root_url

            # If not running `mkdocs serve`, apply local and version overrides
            if not self.is_serving:
                if locale_override:
                    if self._url_versioning_scheme is UrlVersioningScheme.LOCALE_AND_VERSION:
                        root_url = replace_locale(root_url, locale_override)
                    else:
                        msg = (
                            f"The locale override {locale_override!r} has been detected in the absolute URL "
                            f"{absolute_url!r}, but the current URL versioning scheme "
                            f"{self._url_versioning_scheme!r} does not include any locale. Make sure "
                            "the resulting resolved URL is correct!\n"
                            "To change URL versioning scheme, set or update the "
                            "'url_versioning_scheme' configuration option."
                        )
                        logger.warning(msg)
                if version_override:
                    if self._url_versioning_scheme is not UrlVersioningScheme.NONE:
                        root_url = replace_version(root_url, version_override)
                    else:
                        msg = (
                            f"The version override {version_override!r} has been detected in the absolute URL "
                            f"{absolute_url!r}, but the current URL versioning scheme "
                            f"{self._url_versioning_scheme!r} does not include any version. Make sure "
                            "the resulting resolved URL is correct!\n"
                            "To change URL versioning scheme, set or update the "
                            "'url_versioning_scheme' configuration option."
                        )
                        logger.warning(msg)
            # Construct the resolved URL
            resolved_url=root_url + '/' + link
            logger.info(f"Replaced absolute url {absolute_url!r} with '{resolved_url}'")
            return f'{attribute}="{resolved_url}"'

        return self.url_regex.sub(_replacer, output)
