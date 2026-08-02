"""End-to-end deterministic production pipeline."""

from pathlib import Path

from app.models import Decision, OutputFile
from app.services.container import Container
from pipeline.metrics import MetricsCollector, PipelineProfiler
from pipeline.output import CSVExporter, OutputGenerator
from pipeline.validation import ValidationEngine


class BatchProcessor:
    """Process message IDs sequentially with a streaming-friendly API."""

    def __init__(self, pipeline: "ExecutionPipeline") -> None:
        self._pipeline = pipeline

    def process(self, message_ids: tuple[str, ...]) -> tuple[Decision, ...]:
        """Process all IDs without retaining intermediate contexts."""
        return tuple(self._pipeline.process_message(message_id) for message_id in message_ids)


class ExecutionPipeline:
    """Assemble existing services into one executable pipeline."""

    def __init__(self, container: Container) -> None:
        self._container = container
        self.metrics = MetricsCollector()
        self._validation = ValidationEngine(container.logger)
        self._output = OutputGenerator()
        self._exporter = CSVExporter()
        self._logger = container.logger

    def process_message(self, message_id: str) -> Decision:
        """Run every frozen phase for one message and validate its decision."""
        with PipelineProfiler(self.metrics, "pipeline"):
            context = self._container.context_builder.build(message_id)
            profile = self._container.personalization_service.build(context)
            evidence = self._container.retrieval_service.retrieve(context, profile)
            features = self._container.feature_engineering_service.build(context, profile, evidence)
            signals = self._container.priority_risk_engine.build(features)
            packet = self._container.decision_orchestrator.build(
                context, profile, evidence, features, signals
            )
            decision = self._container.router_agent.decide(packet)
            checked = self._validation.validate_or_fallback(decision, packet)
            self.metrics.messages += 1
            self.metrics.latencies_ms.append(checked.latency_ms)
            self.metrics.token_usage += checked.token_usage
            self.metrics.repairs += checked.repair_count
            self.metrics.estimated_cost += checked.estimated_cost
            self._logger.info("pipeline_message_completed", message_id=message_id)
            return checked

    def run(self, message_ids: tuple[str, ...]) -> OutputFile:
        """Process IDs and build the official output model."""
        self._logger.info("pipeline_started", message_count=len(message_ids))
        decisions = BatchProcessor(self).process(message_ids)
        output = self._output.build(decisions)
        self._logger.info("output_generated", row_count=len(output.rows))
        return output

    def export(self, message_ids: tuple[str, ...], path: Path = Path("output.csv")) -> Path:
        """Run the pipeline and write the official CSV."""
        return self._exporter.export(self.run(message_ids), path)
