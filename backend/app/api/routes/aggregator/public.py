from fastapi import APIRouter

from . import dependencies as aggregator_dependencies
from . import schemas

router = APIRouter(prefix="/v1/public/newspapers", tags=["public-newspapers"])


@router.get(
    "/{public_token}",
    response_model=schemas.NewspaperDetail,
)
def get_public_newspaper(public_token: str) -> schemas.NewspaperDetail:
    return aggregator_dependencies.aggregator_service.get_public_newspaper(public_token)


__all__ = ["router"]
