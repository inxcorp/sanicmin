from sanicmin import SanicMin
from sanic import Sanic
from sanic import Request
from sanic import HTTPResponse
from sanic import response
from aiofiles import open as aioopen
from os.path import split
from os.path import join


app = Sanic(name="example-app")


# attach SanicMin to your Sanic app in 2 lines of code
sanic_min = SanicMin(enable_storage=True)
sanic_min.apply_middleware(app=app)


def fullpath(filename: str) -> str:
    return join(split(__file__)[0], filename)


async def read_file(path: str) -> str:
    async with aioopen(file=fullpath(filename=path), mode="r") as file:
        return await file.read()


@app.route(uri="/html", methods=["GET"])
async def html(request: Request) -> HTTPResponse:
    return response.text(
        body=await read_file(path="./examples/example.html"),
        content_type="text/html"
    )


@app.route(uri="/css", methods=["GET"])
async def css(request: Request) -> HTTPResponse:
    return response.text(
        body=await read_file(path="./examples/example.css"),
        content_type="text/css"
    )


@app.route(uri="/javascript", methods=["GET"])
async def javascript(request: Request) -> HTTPResponse:
    return response.text(
        body=await read_file(path="./examples/example.js"),
        content_type="text/javascript",
    )


@app.route(uri="/json", methods=["GET"])
async def json(request: Request) -> HTTPResponse:
    return response.text(
        body=await read_file(path="./examples/example.json"),
        content_type="application/json",
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=80)
