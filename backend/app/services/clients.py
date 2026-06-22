from app.db.config import DatabaseConfig
from app.db.transactions import transaction
from app.domain.clients import ClientDraft
from app.models.client import Client
from app.repositories.audit import AuditLogRepository
from app.repositories.clients import ClientNotFoundError, ClientRepository


class ClientService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config
        self.repository = ClientRepository(config)
        self.audit = AuditLogRepository(config)

    def create_client(self, draft: ClientDraft) -> Client:
        with transaction(self.config) as connection:
            client = self.repository.create(draft, connection=connection)
            self.audit.create_log(action="client.created", entity_type="client", entity_id=str(client.id), summary=f"Client created: {client.full_name}", connection=connection)
        return client

    def get_client(self, client_id: int) -> Client:
        return self.repository.get_by_id(client_id)

    def list_clients(self, *, include_inactive: bool = False) -> list[Client]:
        return self.repository.list_clients(include_inactive=include_inactive)

    def update_client(self, client_id: int, draft: ClientDraft) -> Client:
        with transaction(self.config) as connection:
            client = self.repository.update_basic(client_id, draft, connection=connection)
            self.audit.create_log(action="client.updated", entity_type="client", entity_id=str(client.id), summary=f"Client updated: {client.full_name}", connection=connection)
        return client

    def deactivate_client(self, client_id: int) -> Client:
        with transaction(self.config) as connection:
            client = self.repository.deactivate(client_id, connection=connection)
            self.audit.create_log(action="client.deactivated", entity_type="client", entity_id=str(client.id), summary=f"Client deactivated: {client.full_name}", connection=connection)
        return client


__all__ = ["ClientNotFoundError", "ClientService"]
