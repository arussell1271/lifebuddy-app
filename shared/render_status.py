import os
from jinja2 import Environment, FileSystemLoader, select_autoescape


_env = None


def _get_env():
    global _env
    if _env is None:
        here = os.path.dirname(__file__)
        _env = Environment(loader=FileSystemLoader(here), autoescape=select_autoescape(["html", "xml"]))
    return _env


def render_status(title: str, subtitle: str, services: list, thresholds: list, footer: str, home_url: str | None = None) -> str:
    """Render the shared status_template.html with provided context.

    Args:
        title: Page title string
        subtitle: Short subtitle string
        services: List of dicts with keys: status_class, status_label, component, detail
        thresholds: List of dicts with keys: color, label, text
        footer: Footer text

    Returns:
        Rendered HTML string
    """
    env = _get_env()
    tmpl = env.get_template("status_template.html")
    return tmpl.render(title=title, subtitle=subtitle, services=services, thresholds=thresholds, footer=footer, home_url=home_url)


def render_landing(title: str, subtitle: str, status_url: str, app_api_calls: list, endpoints: list | None = None) -> str:
    """Render a simple Engine landing page listing the internal status URL and App API calls.

    Args:
        title: Page title
        subtitle: Short subtitle
        status_url: URL to engine internal status (relative or absolute)
        app_api_calls: List of dicts with keys `path` and `desc` representing App endpoints

    Returns:
        Rendered HTML string
    """
    env = _get_env()
    tmpl = env.get_template("engine_landing.html")
    return tmpl.render(title=title, subtitle=subtitle, status_url=status_url, app_api_calls=app_api_calls, endpoints=endpoints or [])
