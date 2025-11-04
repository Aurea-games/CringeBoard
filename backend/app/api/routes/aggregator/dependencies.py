from app.api.routes.auth.dependencies import auth_repository

from .repository import AggregatorRepository
from .services import AggregatorService

aggregator_repository = AggregatorRepository()
aggregator_service = AggregatorService(aggregator_repository, auth_repository)

__all__ = ["aggregator_repository", "aggregator_service"]
