from importlib import import_module

from flask import Flask, render_template, request
from flask.blueprints import Blueprint
from mvc_flask import plugins

from .router import Router


class FlaskMVC:
    def __init__(self, app: Flask = None, path="app"):
        if app is not None:
            self.init_app(app, path)

    def init_app(self, app: Flask = None, path="app"):
        self.hook = Hook()
        self.path = path

        app.template_folder = "views"

        self.register_blueprint(app)
        plugins.register(app)

    def register_blueprint(self, app: Flask):
        # load routes defined from users
        import_module(f"{self.path}.routes")

        for route in Router._method_route().items():
            controller = route[0]
            blueprint = Blueprint(controller, controller)

            obj = import_module(
                f"{self.path}.controllers.{controller}_controller"
            )
            view_func = getattr(obj, f"{controller.title()}Controller")

            self.hook.register(view_func, blueprint)

            for resource in route[1]:
                blueprint.add_url_rule(
                    rule=resource.path,
                    endpoint=resource.action,
                    view_func=getattr(view_func(), resource.action),
                    methods=resource.method,
                )

            app.register_blueprint(blueprint)


class Hook:
    def register(self, ctrl, blueprint):
        accept_attributes = [
            "before_request",
            "after_request",
            "teardown_request",
            "after_app_request",
            "before_app_request",
            "teardown_app_request",
            "before_app_first_request",
        ]
        attrs = [attr for attr in dir(ctrl()) if attr in accept_attributes]
        if attrs:
            for attr in attrs:
                values = getattr(ctrl(), attr)

                for value in values:
                    hook_method = getattr(ctrl(), value)
                    getattr(blueprint, attr)(hook_method)
