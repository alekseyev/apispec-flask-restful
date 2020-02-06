# -*- coding: utf-8 -*-
"""Flask-RESTful plugin"""

import re

from apispec import APISpec, BasePlugin, yaml_utils
from apispec.exceptions import APISpecError


_RE_URL = re.compile(r'<(?:[^:<>]+:)?([^<>]+)>')


class FlaskRestfulPlugin(BasePlugin):
    """APISpec plugin for Flask-restful"""

    @staticmethod
    def flaskpath2openapi(path):
        """Convert a Flask URL rule to an OpenAPI-compliant path.
        :param str path: Flask path template.
        """
        return _RE_URL.sub(r'{\1}', path)

    @staticmethod
    def _deduce_path(resource, **kwargs):
        """Find resource path using provided API or path itself"""
        api = kwargs.get('api', None)
        if not api:
            # flask-restful resource url passed
            return kwargs.get('path')

        # flask-restful API passed
        # Require MethodView
        if not getattr(resource, 'endpoint', None):
            raise APISpecError('Flask-RESTful resource needed')

        if api.blueprint:
            # it is required to have Flask app to be able enumerate routes
            app = kwargs.get('app')
            if app:
                for rule in app.url_map.iter_rules():
                    if rule.endpoint.endswith('.' + resource.endpoint):
                        break
                else:
                    raise APISpecError(
                        'Cannot find blueprint resource {}'.format(resource.endpoint)
                    )
            else:
                # Application not initialized yet, fallback to path
                return kwargs.get('path')

        else:
            for rule in api.app.url_map.iter_rules():
                if rule.endpoint == resource.endpoint:
                    rule.endpoint.endswith('.' + resource.endpoint)
                    break
            else:
                raise APISpecError('Cannot find resource {}'.format(resource.endpoint))

        return rule.rule

    def path_helper(self, **kwargs):
        """Extracts swagger spec from `flask-restful` methods."""
        resource = kwargs.pop('resource')
        operations = kwargs.pop('operations')
        path = self._deduce_path(resource, **kwargs)
        path = self.flaskpath2openapi(path)

        for method in resource.methods:
            docstring = getattr(resource, method.lower()).__doc__
            method_name = method.lower()
            operations[method_name] = (
                yaml_utils.load_yaml_from_docstring(docstring) or {}
            )

        return path
