from dataclasses import dataclass


@dataclass(frozen=True)
class ComponentConfig:
    id: str
    name: str
    baseUrl: str
    statusEndpoint: str
    frequency: str
    systemId: str
    ref: str
    expectedTime: str
    timeout: str


@dataclass(frozen=True)
class SystemConfig:
    id: str
    name: str
    ref: str
