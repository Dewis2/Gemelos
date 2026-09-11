from fastapi import Request

from adapters.inbound.api.container import ApplicationContainer


def get_container(request: Request) -> ApplicationContainer:
    return request.app.state.container
