"""
One error format for every failure, so client code needs one error handler:

    {"error": {"code": "invalid_api_key", "message": "...", "details": {...}}}

`code` is stable (programs check it); `message` is for humans.
"""
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class APIError(Exception):
    def __init__(self, status: int, code: str, message: str, details: dict | None = None,
                 headers: dict | None = None):
        self.status, self.code, self.message = status, code, message
        self.details, self.headers = details, headers


def error_body(code: str, message: str, details: dict | None = None) -> dict:
    body = {"code": code, "message": message}
    if details:
        body["details"] = details
    return {"error": body}


def install_handlers(app):
    @app.exception_handler(APIError)
    async def _api_error(_: Request, exc: APIError):
        return JSONResponse(error_body(exc.code, exc.message, exc.details), status_code=exc.status,
                            headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        problems = [{"where": ".".join(str(p) for p in e.get("loc", [])), "problem": e.get("msg")}
                    for e in exc.errors()]
        return JSONResponse(error_body("invalid_request", "The request body is not valid JSON of the "
                                       "expected shape.", {"problems": problems}), status_code=400)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException):
        code = {404: "not_found", 405: "method_not_allowed"}.get(exc.status_code, "http_error")
        return JSONResponse(error_body(code, str(exc.detail)), status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception):
        # Never leak internals (stack traces, SQL) to clients; the log has the details.
        import logging
        logging.getLogger("app").exception("unhandled error")
        return JSONResponse(error_body("internal_error", "Something went wrong on our side. "
                                       "Please retry; if it persists, contact support."), status_code=500)
