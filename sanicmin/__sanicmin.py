from htmlmin import minify as html_min
from rcssmin import cssmin as css_min
from rjsmin import jsmin as js_min
from .__jsonmin import json_min
from sanic import Sanic
from sanic import HTTPResponse
from sanic import Request
from typing import Callable
from uuid import UUID
from uuid import NAMESPACE_URL
from hashlib import sha1
from os.path import join
from os.path import isfile
from os.path import isdir
from os import listdir
from os import remove
from aiofiles import open as asyncopen
from sys import getsizeof


CONTENT_TYPES = {
    "html": ["text/html"],
    "css": ["text/css"],
    "javascript": ["text/javascript"],
    "json": ["application/json"],
}


class MemoryAmount:
    # amount in bytes
    def __init__(self, amount: int) -> None:
        self.__amount = amount

    @property
    def amount(self) -> int:
        return self.__amount

    @staticmethod
    def as_bytes(amount: int) -> "MemoryAmount":
        return MemoryAmount(amount=amount)

    @staticmethod
    def as_kbytes(amount: int) -> "MemoryAmount":
        return MemoryAmount(amount=amount * 1_024)

    @staticmethod
    def as_mbytes(amount: int) -> "MemoryAmount":
        return MemoryAmount(amount=amount * 1_048_576)

    @staticmethod
    def as_gbytes(amount: int) -> "MemoryAmount":
        return MemoryAmount(amount=amount * 1_073_741_824)


class SanicMin:
    def __init__(
        self,
        # content types
        html: bool = True,
        css: bool = True,
        javascript: bool = True,
        json: bool = True,
        # other options
        enable_caching: bool = False,
        cache_dir: str | None = None,
        min_filter: Callable | None = None,
        max_content_size: MemoryAmount | None = None,
    ) -> None:
        if enable_caching and not isdir(s=cache_dir):
            raise NotADirectoryError(
                "cache_dir must be a valid directory if caching is enabled"
            )

        self.__html = html
        self.__css = css
        self.__javascript = javascript
        self.__json = json
        self.__enable_caching = enable_caching
        self.__cache_dir = cache_dir
        self.__min_filter = min_filter
        self.__max_content_size = max_content_size

    async def get_cache(self, cache_uuid: str) -> str | None:
        try:
            filepath = join(self.__cache_dir, cache_uuid + ".bin")

            if isfile(path=filepath):
                async with asyncopen(file=filepath, mode="r") as file:
                    return await file.read()

        except:
            pass

        return None

    async def write_cache(self, cache_uuid: str, content: str) -> None:
        if await self.is_cached(cache_uuid=cache_uuid):
            raise FileExistsError(
                f"cache file with UUID {cache_uuid} is already exists"
            )

        try:
            filepath = join(self.__cache_dir, cache_uuid + ".bin")

            async with asyncopen(file=filepath, mode="w") as file:
                await file.write(content)

        except:
            pass

    async def is_cached(self, cache_uuid: str) -> bool:
        try:
            filepath = join(self.__cache_dir, cache_uuid + ".bin")
            return isfile(path=filepath)

        except:
            pass

        return False

    async def clear_cache(self) -> None:
        if not self.__enable_caching:
            raise ValueError("cannot clear cache if caching is disabled")

        for filename in listdir(self.__cache_dir):
            if filename.split(".")[-1] == "bin":
                remove(path=join(self.__cache_dir, filename))

    async def minify(self, content_type: str, content: str, cache_uuid: str) -> str:
        if (
            self.__max_content_size
            and getsizeof(obj=content) > self.__max_content_size.amount
        ):
            return content

        if self.__enable_caching and await self.is_cached(cache_uuid=cache_uuid):
            return await self.get_cache(cache_uuid=cache_uuid)

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

        if (
            modified
            and self.__enable_caching
            and not await self.is_cached(cache_uuid=cache_uuid)
        ):
            await self.write_cache(cache_uuid=cache_uuid, content=minified)

        return minified

    async def minify_request(
        self, content_type: str, content: str, request: Request, response: HTTPResponse
    ) -> str:
        if self.__min_filter and not self.__min_filter(request, response):
            return content

        if (
            self.__max_content_size
            and getsizeof(obj=content) > self.__max_content_size.amount
        ):
            return content

        if self.__enable_caching:
            storage_hash = sha1(
                NAMESPACE_URL.bytes + bytes(request.url, "utf-8")
            ).digest()
            storage_uuid = str(UUID(bytes=storage_hash[:16], version=5))

        else:
            storage_hash, storage_uuid = None, None

        return await self.minify(
            content_type=content_type,
            content=content,
            cache_uuid=storage_uuid,
        )

    def create_middleware(self) -> Callable:
        async def middleware(request: Request, response: HTTPResponse) -> None:
            try:
                content = response.body.decode("utf-8")
                content_type = response.content_type.split(";")[0]

                minified = await self.minify_request(
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
