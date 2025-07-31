from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth_service import AuthService
from app.schemas.provider_schema import (
    ProviderLoginRequest,
    ProviderLoginResponse,
    ErrorResponse,
)
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/v1/provider", tags=["Provider Auth"])


@router.post(
    "/login",
    response_model=ProviderLoginResponse,
    responses={
        401: {"model": ErrorResponse},
        423: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
    },
)
def provider_login(
    request: Request, login_data: ProviderLoginRequest, db: Session = Depends(get_db)
):
    auth_service = AuthService(db)
    client_ip = request.client.host
    result, error_code = auth_service.login(
        identifier=login_data.identifier,
        password=login_data.password,
        remember_me=login_data.remember_me,
        client_ip=client_ip,
    )
    if result:
        return ProviderLoginResponse(
            success=True, message="Login successful", data=result
        )
    if error_code == "INVALID_CREDENTIALS":
        return JSONResponse(
            status_code=401,
            content=ErrorResponse(
                message="Invalid credentials", error_code=error_code
            ).dict(),
        )
    if error_code == "ACCOUNT_LOCKED":
        return JSONResponse(
            status_code=423,
            content=ErrorResponse(
                message="Account locked due to failed attempts", error_code=error_code
            ).dict(),
        )
    if error_code == "NOT_VERIFIED_OR_INACTIVE":
        return JSONResponse(
            status_code=403,
            content=ErrorResponse(
                message="Account not verified or inactive", error_code=error_code
            ).dict(),
        )
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            message="Internal server error", error_code="INTERNAL_ERROR"
        ).dict(),
    )


# TODO: Implement /refresh, /logout, /logout-all endpoints
