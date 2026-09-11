import os
import re

import mkdocs.plugins
from mkdocs.config import config_options as c
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.exceptions import ConfigurationError

logger = mkdocs.plugins.get_plugin_logger(__name__)


class Config(mkdocs.config.base.Config):
    root_url = c.Type(str, default="")
    attributes = c.Type(list, default=["href", "src", "data"])
    prefix = c.Type(str, default="/")


class ResolveAbsoluteUrlsPlugin(mkdocs.plugins.BasePlugin[Config]):
    # Matches an optional `!locale` and/or `@version` override at the start of a
    # resolved absolute url, e.g. `!fr/@v2.0/my/page` -> locale="fr", version="v2.0", path="my/page"
    _OVERRIDE_RE = re.compile(
        r"^(?:!(?P<locale>[^/]+)/)?(?:@(?P<version>[^/]+)/)?(?P<path>.*)$", re.DOTALL
    )

    def on_config(self, config: MkDocsConfig) -> MkDocsConfig:
        attributes = (re.escape(attr) for attr in self.config["attributes"])
        self.prefix = re.escape(self.config["prefix"])
        regex_parts = [
            r"(", # capturing group 1
            "|".join(attributes), # attributes
            r")", # end of capturing group 1
            r"\s*=\s*", # equals sign with optional whitespace
            r"([\"'])", # quote with capturing group 2
            self.prefix, # url prefix
            r"([^\"']*)", # remainder of the url with capturing group 3
            r"\2", # matching quote
        ]
        regex = "".join(regex_parts)
        self._regex = re.compile(regex, re.IGNORECASE)

        root_url = self.config["root_url"]
        if not root_url:
            root_url = os.environ.get("READTHEDOCS_CANONICAL_URL")
        if not root_url:
            raise ConfigurationError(
                "The 'resolve-absolute-urls' plugin requires a 'root_url' to be configured, "
                "or the 'READTHEDOCS_CANONICAL_URL' environment variable to be set."
            )
        self._root_url = root_url.rstrip("/")
        # Current version/locale of the build, used as defaults when not overridden in the link.
        self._env_version = os.environ.get("READTHEDOCS_VERSION")
        self._env_language = os.environ.get("READTHEDOCS_LANGUAGE")
        if not self._env_version or not self._env_language:
            raise ConfigurationError(
                "The 'resolve-absolute-urls' plugin requires the 'READTHEDOCS_VERSION' and "
                "'READTHEDOCS_LANGUAGE' environment variables to be set."
            )
        return config

    def on_post_page(self, output, page, config):
        def _replacer(match):
            attribute = match.group(1)
            remainder = match.group(3)
            override = self._OVERRIDE_RE.match(remainder)
            locale = override.group("locale") or self._env_language
            version = override.group("version") or self._env_version
            path = override.group("path")

            segments = [self._root_url]
            if locale:
                segments.append(locale)
            if version:
                segments.append(version)
            new_url = "/".join(segments) + "/" + path

            logger.info(f"Replacing absolute url '{self.prefix}{remainder}' with '{new_url}'")
            return f'{attribute}="{new_url}"'

        return self._regex.sub(_replacer, output)
