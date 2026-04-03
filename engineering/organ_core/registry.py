"""Processor Registry — the genome of available neuron types.

Processors register themselves here. Organs can instantiate
processors by name from the registry, enabling on-demand
addition of new capabilities.
"""
from typing import Type
from organ_core.processor import Processor


_registry: dict[str, Type[Processor]] = {}


def register(processor_class: Type[Processor]) -> Type[Processor]:
    """Register a processor class. Can be used as a decorator.

    @register
    class MyProcessor(Processor):
        name = "my_proc"
        ...
    """
    _registry[processor_class.name] = processor_class
    return processor_class


def create(name: str, **kwargs) -> Processor:
    """Create a processor instance by registered name.

    Raises:
        KeyError: If name not registered.
    """
    if name not in _registry:
        raise KeyError(
            f"No processor registered as '{name}'. "
            f"Available: {list(_registry.keys())}"
        )
    return _registry[name](**kwargs)


def available() -> list[dict]:
    """List all registered processor types."""
    return [
        {"name": cls.name, "description": cls.description}
        for cls in _registry.values()
    ]
