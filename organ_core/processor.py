"""Processor — the neuron interface.

Every processing unit in the nervous system implements this interface.
Processors transform data flowing through a Pipeline, adding fields
without removing upstream data. Like neurons: receive, transform, pass on.
"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from organ_core.context import PipelineContext


class Processor(ABC):
    """A single processing unit in the pipeline. The neuron."""

    name: str = ""
    description: str = ""

    @abstractmethod
    def process(self, data: dict, context: 'PipelineContext') -> dict:
        """Transform data. Add fields, enrich, classify.

        Must return the data dict (modified in place or new).
        Should never remove fields added by upstream processors.
        """
        ...

    def startup(self) -> None:
        """Called once when processor is added to a pipeline.

        Use for lazy model loading, resource allocation, etc.
        """
        pass

    def shutdown(self) -> None:
        """Called when processor is removed from a pipeline.

        Use for resource cleanup.
        """
        pass
