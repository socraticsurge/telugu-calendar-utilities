"""Authenticated FastAPI boundary for Vercel-hosted computations."""

import hmac
import logging
import os
import re
import uuid

from fastapi import Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.exceptions import HTTPException as StarletteHTTPException

from telugu_panchangam import __version__
from telugu_panchangam.api import CONTRACT_VERSION
from telugu_panchangam.api import service
from telugu_panchangam.api.models import (
    MuhurtamSearchRequest,
    PanchangamDayRequest,
    PanchangamRangeRequest,
    RasiPhalaluRequest,
    TarabalamRequest,
)

_log = logging.getLogger(__name__)
_bearer = HTTPBearer(auto_error=False)
_REQUEST_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")
_MAX_REQUEST_BYTES = 65_536

app = FastAPI(
    title="Telugu Calendar API",
    version=CONTRACT_VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", uuid.uuid4().hex)


def _error_response(request: Request, status_code: int, code: str, message: str):
    return JSONResponse(
        status_code=status_code,
        content={
            "contract_version": CONTRACT_VERSION,
            "request_id": _request_id(request),
            "error": {"code": code, "message": message},
        },
    )


@app.middleware("http")
async def request_boundary(request: Request, call_next):
    supplied_id = request.headers.get("x-request-id", "")
    request.state.request_id = supplied_id if _REQUEST_ID.fullmatch(supplied_id) else uuid.uuid4().hex

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > _MAX_REQUEST_BYTES:
                return _error_response(request, 413, "payload_too_large", "Request body is too large.")
        except ValueError:
            return _error_response(request, 400, "invalid_content_length", "Invalid request metadata.")
    if request.method == "POST" and request.url.path.startswith("/v1/"):
        content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            return _error_response(request, 415, "unsupported_media_type", "Content-Type must be application/json.")
        if len(await request.body()) > _MAX_REQUEST_BYTES:
            return _error_response(request, 413, "payload_too_large", "Request body is too large.")

    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Contract-Version"] = CONTRACT_VERSION
    response.headers["Cache-Control"] = "private, no-store"
    return response


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return _error_response(request, exc.status_code, exc.code, exc.message)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, _exc: RequestValidationError):
    return _error_response(request, 422, "invalid_request", "Request validation failed.")


@app.exception_handler(StarletteHTTPException)
async def safe_http_error_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return _error_response(request, 404, "not_found", "Endpoint not found.")
    if exc.status_code == 405:
        return _error_response(request, 405, "method_not_allowed", "Method not allowed.")
    return _error_response(request, exc.status_code, "request_failed", "Request could not be completed.")


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    # Do not log exception messages: upstream libraries can include submitted
    # city/profile values. The request ID and exception class are sufficient to
    # correlate with allowlisted operational telemetry.
    _log.error(
        "api request failed",
        extra={"request_id": _request_id(request), "error_type": type(exc).__name__},
    )
    return _error_response(request, 500, "calculation_failed", "Calculation could not be completed.")


def require_service_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    expected = os.environ.get("PANCHANGAM_API_TOKEN")
    if not expected or len(expected) < 32:
        raise ApiError(503, "service_not_configured", "Service authentication is unavailable.")
    supplied = credentials.credentials if credentials and credentials.scheme.lower() == "bearer" else ""
    if not supplied or not hmac.compare_digest(supplied, expected):
        raise ApiError(401, "unauthorized", "Valid service authentication is required.")


def _engine(system: str, ayanamsa: str) -> dict:
    return {
        "package": "mcp-server-panchangam",
        "version": __version__,
        "system": system,
        "ayanamsa": ayanamsa,
    }


def _envelope(request: Request, data: dict, system: str, ayanamsa: str,
              evaluated: list[str], not_evaluated: list[str], warnings: list[str] | None = None):
    provenance = data.get("provenance", [])
    if isinstance(provenance, dict):
        provenance = [provenance]
    return {
        "contract_version": CONTRACT_VERSION,
        "request_id": _request_id(request),
        "engine": _engine(system, ayanamsa),
        "data": data,
        "evidence": {
            "evaluated_factors": evaluated,
            "not_evaluated": not_evaluated,
            "provenance": provenance,
        },
        "warnings": warnings or [],
    }


def _safe_compute(operation):
    try:
        return operation()
    except service.CalculationError as exc:
        raise ApiError(422, "calculation_rejected", "Calculation could not be completed for this request.") from exc


@app.get("/health")
def health(request: Request):
    return {
        "status": "ok",
        "contract_version": CONTRACT_VERSION,
        "engine": {"package": "mcp-server-panchangam", "version": __version__},
        "request_id": _request_id(request),
    }


@app.get("/v1/catalog", dependencies=[Depends(require_service_token)])
def get_catalog(request: Request, locale: str = Query(default="en", pattern="^en$")):
    data = service.catalog()
    return _envelope(request, data, "catalog", "catalog", ["catalog"], [])


@app.post("/v1/panchangam/day", dependencies=[Depends(require_service_token)])
def get_panchangam_day(request: Request, payload: PanchangamDayRequest):
    data = _safe_compute(lambda: service.panchangam_day(payload))
    return _envelope(
        request, data, payload.system, payload.ayanamsa,
        [
            "pancha_anga",
            "day_windows",
            "special_days",
            "horas",
            "choghadiya",
            "lagna_transitions",
        ],
        ["participant_suitability", "natal_chart"],
    )


@app.post("/v1/panchangam/range", dependencies=[Depends(require_service_token)])
def get_panchangam_range(request: Request, payload: PanchangamRangeRequest):
    data = _safe_compute(lambda: service.panchangam_range(payload))
    return _envelope(
        request, data, payload.system, payload.ayanamsa,
        ["pancha_anga", "day_windows", "special_days"],
        ["intraday_horas", "lagna_transitions", "participant_suitability"],
    )


@app.post("/v1/rasi-phalalu", dependencies=[Depends(require_service_token)])
def get_rasi_phalalu(request: Request, payload: RasiPhalaluRequest):
    data = _safe_compute(lambda: service.rasi_phalalu(payload))
    evaluated = ["gochara", "chandrabalam"]
    if payload.janma_nakshatra:
        evaluated.append("tarabalam")
    return _envelope(
        request, data, "drik", payload.ayanamsa, evaluated,
        ["full_natal_chart", "dasha", "personal_consultation"],
    )


@app.post("/v1/tarabalam", dependencies=[Depends(require_service_token)])
def get_tarabalam(request: Request, payload: TarabalamRequest):
    data = _safe_compute(lambda: service.tarabalam(payload))
    evaluated = ["tarabalam"]
    if any(participant.janma_rasi for participant in payload.participants):
        evaluated.append("chandrabalam")
    return _envelope(
        request, data, payload.system, payload.ayanamsa, evaluated,
        ["natal_chart", "dasha", "activity_specific_muhurta"],
        ["Tarabalam day comparison currently uses the canonical Lahiri tool path."],
    )


@app.post("/v1/muhurtam/search", dependencies=[Depends(require_service_token)])
def search_muhurtam(request: Request, payload: MuhurtamSearchRequest):
    data = _safe_compute(lambda: service.muhurtam(payload))
    evaluated = ["panchangam", "activity_rules", "avoid_windows", "slot_quality"]
    not_evaluated = ["full_election_chart", "dasha", "manual_prerequisites"]
    if payload.participants:
        evaluated.extend(["tarabalam", "chandrabalam", "lagna_from_supplied_context"])
    else:
        not_evaluated.extend(["tarabalam", "chandrabalam", "participant_lagna"])
    return _envelope(
        request, data, payload.system, payload.ayanamsa,
        evaluated, not_evaluated,
    )
