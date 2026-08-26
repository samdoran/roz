"""Workflow registry and protocol for downstream-release."""

from roz.workflows.goose import GooseWorkflow
from roz.workflows.protocol import WorkflowProtocol


WORKFLOW_MAP: dict[str, WorkflowProtocol] = {
    "goose": GooseWorkflow(),
}
