from htmlmin import minify as html_min
from cssmin import cssmin as css_min
from jsmin import jsmin as js_min
from .__jsonmin import json_min
from sanic import Sanic
from sanic import HTTPResponse
from sanic import Request
from typing import Callable


CONTENT_TYPES = {
    "html": ["text/html"],
    "css": ["text/css"],
    "javascript": ["text/javascript"],
    "json": ["application/json"],
}


class SanicMin:
    def __init__(
        self,
        html: bool = True,
        css: bool = True,
        javascript: bool = True,
        json: bool = True,
        enable_storage: bool = False,
        middleware_filter: Callable | None = None,
    ) -> None:
        self.__html = html
        self.__css = css
        self.__javascript = javascript
        self.__json = json
        self.__enable_storage = enable_storage
        self.__storage = {}
        self.__middleware_filter = middleware_filter

    def minify(
        self, content_type: str, content: str, request: Request, response: HTTPResponse
    ) -> str:
        if self.__middleware_filter and not self.__middleware_filter(request, response):
            return content

        if self.__enable_storage and request.path in self.__storage:
            return self.__storage.get(request.path)

        if content_type in CONTENT_TYPES.get("html", []) and self.__html:
            minified = html_min(
                content,
                remove_comments=True,
                remove_empty_space=True,
                remove_all_empty_space=True,
                reduce_empty_attributes=True,
                reduce_boolean_attributes=True,
            )
            modified = True

        elif content_type in CONTENT_TYPES.get("css", []) and self.__css:
            minified = css_min(content)
            modified = True

        elif content_type in CONTENT_TYPES.get("javascript", []) and self.__javascript:
            minified = js_min(content)
            modified = True

        elif content_type in CONTENT_TYPES.get("json", []) and self.__json:
            minified = json_min(content)
            modified = True

        else:
            minified = content
            modified = False

        if modified and self.__enable_storage and request.path not in self.__storage:
            self.__storage.update({request.path: minified})

        return minified

    def create_middleware(self) -> Callable:
        def middleware(request: Request, response: HTTPResponse) -> None:
            try:
                content = response.body.decode()
                content_type = response.content_type.split(";")[0]

                minified = self.minify(
                    content_type=content_type,
                    content=content,
                    request=request,
                    response=response,
                )
                response.body = minified.encode()

            except Exception as exc:
                pass

        return middleware

    def apply_middleware(self, app: Sanic, priority: int = 0) -> None:
        app.middleware(
            self.create_middleware(), attach_to="response", priority=priority
        )
