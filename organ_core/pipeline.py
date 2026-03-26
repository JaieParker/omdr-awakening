"""Pipeline — the nerve pathway.

An ordered chain of Processors. Data flows through each processor
in sequence, enriched at each step. Processors can be added, removed,
and reordered at runtime — neuroplasticity.
"""
import time
from typing import Optional
from organ_core.processor import Processor
from organ_core.context import PipelineContext


class Pipeline:
    """Ordered chain of processors. Add/remove/reorder at runtime."""

    def __init__(self, name: str):
        self.name = name
        self.processors: list[Processor] = []
        self.context = PipelineContext()

    def _find_index(self, name: str) -> int:
        """Find processor index by name. Raises KeyError if not found."""
        for i, p in enumerate(self.processors):
            if p.name == name:
                return i
        raise KeyError(f"No processor named '{name}' in pipeline '{self.name}'")

    def add(self, processor: Processor,
            after: Optional[str] = None,
            before: Optional[str] = None) -> None:
        """Insert processor into the chain.

        Args:
            processor: The processor to add.
            after: Insert after the processor with this name.
            before: Insert before the processor with this name.
            If neither specified, appends to end.

        Raises:
            ValueError: If a processor with the same name already exists.
            KeyError: If after/before name not found.
        """
        # Check for duplicate names
        for p in self.processors:
            if p.name == processor.name:
                raise ValueError(
                    f"Processor '{processor.name}' already exists in pipeline '{self.name}'"
                )

        if after is not None:
            idx = self._find_index(after)
            self.processors.insert(idx + 1, processor)
        elif before is not None:
            idx = self._find_index(before)
            self.processors.insert(idx, processor)
        else:
            self.processors.append(processor)

        processor.startup()

    def remove(self, name: str) -> Processor:
        """Remove and return a processor by name. Calls shutdown().

        Raises:
            KeyError: If name not found.
        """
        idx = self._find_index(name)
        processor = self.processors.pop(idx)
        processor.shutdown()
        return processor

    def reorder(self, names: list[str]) -> None:
        """Set explicit processor order by name list.

        Raises:
            KeyError: If any name in the list is not in the pipeline.
        """
        by_name = {p.name: p for p in self.processors}
        new_order = []
        for name in names:
            if name not in by_name:
                raise KeyError(f"No processor named '{name}' in pipeline '{self.name}'")
            new_order.append(by_name[name])
        self.processors = new_order

    def run(self, initial_data: Optional[dict] = None) -> dict:
        """Run data through all processors in order.

        Each processor enriches the data dict. Returns the final enriched dict.
        Records timing stats for each processor.
        """
        data = initial_data if initial_data is not None else {}

        for processor in self.processors:
            t0 = time.perf_counter()
            data = processor.process(data, self.context)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            self.context.record_stat(processor.name, elapsed_ms)

        return data

    def list_processors(self) -> list[dict]:
        """Return name, description, and stats for each processor."""
        result = []
        for p in self.processors:
            stats = self.context.get_stats(p.name)
            result.append({
                "name": p.name,
                "description": p.description,
                "stats": stats,
            })
        return result
