from fastapi import APIRouter, HTTPException, status

from app.domain.errors import DomainValidationError
from app.domain.orders import OrderDraft
from app.models.order import Order, OrderStatus
from app.repositories.client_recipes import ClientRecipeNotFoundError
from app.repositories.clients import ClientNotFoundError
from app.repositories.orders import OrderNotFoundError
from app.repositories.packaging_items import PackagingItemNotFoundError
from app.repositories.recipes import RecipeVersionNotFoundError
from app.schemas.orders import OrderCreateRequest, OrderResponse, OrdersResponse, OrderUpdateRequest
from app.services.orders import OrderClientInactiveError, OrderClientRecipeInactiveError, OrderClientRecipeMismatchError, OrderLifecycleError, OrderPackagingInactiveError, OrderService

router = APIRouter(tags=["orders"])


@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreateRequest):
    draft = OrderDraft.create(
        **payload.model_dump(),
        status=OrderStatus.NEW,
        produced_at=None,
        delivered_at=None,
    )
    return _handle_write(lambda: _response(OrderService().create(draft)))


@router.get("/orders", response_model=OrdersResponse)
def list_orders(include_inactive: bool = True, status: str | None = None, client_id: int | None = None):
    try:
        return OrdersResponse(orders=[_response(o) for o in OrderService().list_orders(include_inactive=include_inactive, status=status, client_id=client_id)])
    except DomainValidationError as exc:
        raise HTTPException(422, detail=exc.issue.__dict__) from exc
    except ValueError as exc:
        raise HTTPException(422, detail=str(exc)) from exc


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int):
    try:
        return _response(OrderService().get_by_id(order_id))
    except DomainValidationError as exc:
        raise HTTPException(422, detail=exc.issue.__dict__) from exc
    except OrderNotFoundError as exc:
        raise HTTPException(404, detail="Order was not found.") from exc


@router.put("/orders/{order_id}", response_model=OrderResponse)
def update_order(order_id: int, payload: OrderUpdateRequest):
    draft = OrderDraft.create(**payload.model_dump())
    return _handle_write(lambda: _response(OrderService().update(order_id, draft)))


@router.post("/orders/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(order_id: int):
    return _handle_write(lambda: _response(OrderService().cancel(order_id)))


@router.post("/orders/{order_id}/archive", response_model=OrderResponse)
def archive_order(order_id: int):
    return _handle_write(lambda: _response(OrderService().archive(order_id)))


@router.get("/clients/{client_id}/orders", response_model=OrdersResponse)
def list_client_orders(client_id: int, include_inactive: bool = True, status: str | None = None):
    try:
        return OrdersResponse(orders=[_response(o) for o in OrderService().list_orders(include_inactive=include_inactive, status=status, client_id=client_id)])
    except DomainValidationError as exc:
        raise HTTPException(422, detail=exc.issue.__dict__) from exc
    except ValueError as exc:
        raise HTTPException(422, detail=str(exc)) from exc


def _handle_write(fn):
    try:
        return fn()
    except DomainValidationError as exc:
        raise HTTPException(422, detail=exc.issue.__dict__) from exc
    except (ClientNotFoundError, RecipeVersionNotFoundError, ClientRecipeNotFoundError, PackagingItemNotFoundError, OrderNotFoundError) as exc:
        raise HTTPException(404, detail="Linked record was not found.") from exc
    except (OrderClientInactiveError, OrderClientRecipeInactiveError, OrderClientRecipeMismatchError, OrderPackagingInactiveError, OrderLifecycleError) as exc:
        raise HTTPException(409, detail=str(exc)) from exc


def _response(o: Order) -> OrderResponse:
    return OrderResponse(**{**o.__dict__, "target_batch_size_value": str(o.target_batch_size_value), "packaging_quantity": None if o.packaging_quantity is None else str(o.packaging_quantity), "sale_price": None if o.sale_price is None else str(o.sale_price)})
