# -*- coding: utf-8 -*-


from functools import wraps
from jinja2 import Environment as jinja_Environment, contextfunction as jinja_contextfunction

from jinja2.nativetypes import NativeEnvironment as jinja_NativeEnvironment

from sanic.response import text as sanic_response_text, \
    html as sanic_response_html, \
    json as sanic_response_json, \
    raw as sanic_response_raw

from ujson import loads as ujson_loads

__version__ = "1.0.5"
__author__ = "tomaszdrozdz"
__author_email__ = "tomasz.drozdz.1@protonmail.com"


@jinja_contextfunction
def get_jinja_template_context(context, key=None):
    context = {k: '"Is callable"' if callable(v) else v
               for k, v in context.items()
               if k not in ["range", "dict", "lipsum", "cycler", "joiner", "namespace"]}

    if key:
        return context.get(key, None)
    else:
        return context


def conf_app(app,
             jinja_template_env_name="JINJA_ENV",
             update_templates_with_its_context=False,
             update_jinja_env_globals_with={},
             *args, **kwargs):
    """Create Jinja template environment, and srotes it in sanic app.config.


    Parameters
    ----------
    app: sanic app instance
    jinja_template_env_name:  str, optional
        jinja template environment instance will be held under
        app.config[jinja_template_env_name].
        This also coresponds to
        jinja_template_env_name in render() function.
    update_templates_with_its_context: bool, default False
        If True then templates context can be accesed from within them
        by using get_template_contex("optional: some_key").
    update_jinja_env_globals_with: dict: default {}
        Provide extra context for templates.
        E.g when set to {'x': 5} then every template can access it with: {{x}}.
    *args, **kwargs:
        are just jijna2.Environment() parameters.

    Returns
    -------
    created Jinja environment template instance."""
    jinja_template_environment = jinja_Environment(*args, **kwargs)

    if update_templates_with_its_context:
        jinja_template_environment.globals.update({'get_template_context': get_jinja_template_context})

    jinja_template_environment.globals.update(update_jinja_env_globals_with)
    app.config[jinja_template_env_name] = jinja_template_environment
    return jinja_template_environment


def render(template,
           render_as,
           update_template_with_its_context=False,
           update_template_globals_with={},
           jinja_template_env_name='JINJA_ENV'):
    """Decorator for Sanic request handler,

    that turns it into function returning generated jinja template,
    as sanic response.

    Decorated function (or method) has to return jinja "context" instance.

    Parameters:
    -----------
    template:  str
        jinja template name.
    render_as: str
        corresponds to sanic.response "kind".
        Possible valuse are: "text", "html", "json", "raw".
    update_template_with_its_context: bool, default False
        If True then template context can be accesed from within it
        by using get_template_contex("optional: some_key").
    update_template_globals_with: dict: default {}
        Provide extra context for template.
        E.g when set to {'x': 5} then template can access it with: {{x}}.
    jinja_template_env_name:  str, optional
        Where jinja template environment instance is held in
        app.config.
        This coresponds to
        jinja_template_env_name in conf_app() function."""

    _sanic_responses = {
        'text': sanic_response_text,
        'html': sanic_response_html,
        'json': sanic_response_json,
        'raw': sanic_response_raw}

    def _decorator(to_decorate):

        @wraps(to_decorate)
        async def _decorated(request, *args, **kwargs):

            _jinja_env = request.app.config[jinja_template_env_name]

            template_context = await to_decorate(request, *args, **kwargs)

            template_renderer = _jinja_env.get_template(template)

            if update_template_with_its_context:
                template_renderer.globals.update({'get_template_context': get_jinja_template_context})

            template_renderer.globals.update(update_template_globals_with)
            template_renderer.globals.update({"request": request})

            if _jinja_env.is_async:
                rendered_template = await template_renderer.render_async(template_context)
            else:
                rendered_template = template_renderer.render(template_context)

            if render_as == "json" \
                    and not isinstance(_jinja_env, jinja_NativeEnvironment):
                rendered_template = ujson_loads(rendered_template)

            return _sanic_responses[render_as](rendered_template)

        return _decorated

    return _decorator
