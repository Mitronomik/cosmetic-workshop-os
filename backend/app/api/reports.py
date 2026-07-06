from fastapi import APIRouter

from app.schemas.reports import FinanceReportResponse, InventoryReportResponse, OrdersReportResponse, OverviewReportResponse, ProductionReportResponse
from app.services.reports import ReportsService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/overview", response_model=OverviewReportResponse)
def get_reports_overview() -> OverviewReportResponse:
    return ReportsService().get_overview()


@router.get("/inventory", response_model=InventoryReportResponse)
def get_inventory_report() -> InventoryReportResponse:
    return ReportsService().get_inventory_report()


@router.get("/orders", response_model=OrdersReportResponse)
def get_orders_report() -> OrdersReportResponse:
    return ReportsService().get_orders_report()


@router.get("/production", response_model=ProductionReportResponse)
def get_production_report() -> ProductionReportResponse:
    return ReportsService().get_production_report()


@router.get("/finance", response_model=FinanceReportResponse)
def get_finance_report() -> FinanceReportResponse:
    return ReportsService().get_finance_report()
