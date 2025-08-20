"""Resource bundle models.

Minimal yet usable bundle types for grouping related HACS resources.
"""

from typing import Any, Literal

from pydantic import Field, model_validator

from .base_resource import BaseResource
from .types import BundleStatus, BundleType
from .workflow import LinkRelation, WorkflowBinding, WorkflowBindingType


# Minimal types for workflow bindings and links used by tests
class Link(BaseResource):
    resource_type: Literal["Link"] = Field(default="Link")
    relation: str = Field(description="Link relation")
    url: str = Field(description="URL")


class BundleEntry(BaseResource):
    resource_type: Literal["BundleEntry"] = Field(default="BundleEntry")

    title: str | None = Field(default=None, description="Entry title")
    tags: list[str] = Field(default_factory=list, description="Entry tags")
    priority: int = Field(default=0, description="Ordering priority")
    # The actual contained resource (FHIR Bundle.entry.resource)
    resource: Any | None = Field(
        default=None, description="The actual resource contained in this entry"
    )
    # Optional reference ID for linking
    contained_resource_id: str | None = Field(
        default=None, description="ID of the contained resource"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary entry metadata")


class ResourceBundle(BaseResource):
    resource_type: Literal["ResourceBundle"] = Field(default="ResourceBundle")
    title: str | None = Field(default=None, description="Bundle title")
    bundle_type: BundleType | None = Field(default=None)
    entries: list[BundleEntry] = Field(default_factory=list, description="Bundle entries")
    status: BundleStatus = Field(default=BundleStatus.DRAFT, description="Bundle lifecycle status")
    # Optional metadata used by tests and utilities
    version: str | None = None
    description: str | None = None
    publisher: str | None = None
    keywords: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    total: int | None = None
    links: list[Link] = Field(default_factory=list)
    workflow_bindings: list[Any] = Field(default_factory=list)

    class UseCase(BaseResource):
        resource_type: Literal["UseCase"] = Field(default="UseCase")
        name: str
        description: str
        examples: list[str] = Field(default_factory=list)
        prerequisites: list[str] = Field(default_factory=list)
        outcomes: list[str] = Field(default_factory=list)
        tags: list[str] = Field(default_factory=list)
        model_config = {"extra": "allow"}

    use_cases: list[UseCase] = Field(default_factory=list)
    updates: list[Any] = Field(default_factory=list)
    quality_score: float | None = None
    maturity_level: str | None = None
    experimental: bool | None = None

    def add_entry(
        self,
        resource: BaseResource,
        title: str | None = None,
        tags: list[str] | None = None,
        priority: int = 0,
    ) -> None:
        entry = BundleEntry(
            resource_type="BundleEntry",
            title=title,
            tags=tags or [],
            priority=priority,
            resource=resource,  # Store the actual resource
            contained_resource_id=getattr(resource, "id", None),
        )
        self.entries.append(entry)

    # Compatibility helpers used by tests (no-op/simple implementations)
    def add_resource(
        self,
        resource: BaseResource,
        title: str | None = None,
        tags: list[str] | None = None,
        priority: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.add_entry(resource, title=title, tags=tags, priority=priority)
        if metadata:
            if not hasattr(self.entries[-1], "metadata"):
                self.entries[-1].metadata = {}
            self.entries[-1].metadata.update(metadata)

    def add_link(self, relation: str, url: str) -> None:
        self.links.append(Link(relation=relation, url=url))

    # Factory function compatibility
    @staticmethod
    def create_resource_stack(
        stack_name: str,
        version: str,
        description: str | None = None,
        resources: list[BaseResource] | None = None,
        publisher: str | None = None,
    ) -> "ResourceBundle":
        bundle = ResourceBundle(
            title=stack_name,
            bundle_type=BundleType.STACK,
            version=version,
            description=description,
            publisher=publisher,
            status=BundleStatus.ACTIVE,
        )
        for res in resources or []:
            bundle.add_resource(res)
        return bundle

    @staticmethod
    def create_search_results_bundle(
        resources: list[BaseResource], total: int, search_url: str
    ) -> "ResourceBundle":
        bundle = ResourceBundle(bundle_type=BundleType.SEARCHSET, version="1.0.0", total=total)
        for res in resources:
            bundle.add_resource(res)
        # Add self link
        bundle.add_link(LinkRelation.SELF, search_url)
        return bundle

    @staticmethod
    def create_workflow_template_bundle(
        template_name: str,
        version: str,
        workflow_id: str,
        template_resources: list[BaseResource],
        description: str | None = None,
    ) -> "ResourceBundle":
        bundle = ResourceBundle(
            title=template_name,
            bundle_type=BundleType.TEMPLATE,
            version=version,
            description=description,
        )
        for res in template_resources:
            bundle.add_resource(res)
        bundle.add_workflow_binding(workflow_id, WorkflowBindingType.OUTPUT_TEMPLATE)
        return bundle

    def get_resources_by_type(self, resource_type: str) -> list[BaseResource]:
        return [
            e.resource
            for e in self.entries
            if getattr(e.resource, "resource_type", None) == resource_type
        ]

    def get_resources_by_tag(self, tag: str) -> list[BaseResource]:
        return [e.resource for e in self.entries if tag in (e.tags or [])]

    def add_workflow_binding(
        self,
        workflow_id: str,
        binding_type: Any,
        workflow_name: str | None = None,
        parameters: dict[str, Any] | None = None,
        priority: int = 0,
        description: str | None = None,
    ) -> None:
        self.workflow_bindings.append(
            WorkflowBinding(
                workflow_id=workflow_id,
                binding_type=binding_type,
                parameters=parameters or {},
                priority=priority,
                description=description,
                workflow_name=workflow_name,
            )
        )

    def get_workflow_bindings_by_type(self, binding_type: Any) -> list[Any]:
        return [
            wb for wb in self.workflow_bindings if getattr(wb, "binding_type", None) == binding_type
        ]

    def add_use_case(
        self,
        name: str,
        description: str,
        examples: list[str] | None = None,
        prerequisites: list[str] | None = None,
        outcomes: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> None:
        self.use_cases.append(
            self.UseCase(
                name=name,
                description=description,
                examples=examples or [],
                prerequisites=prerequisites or [],
                outcomes=outcomes or [],
                tags=tags or [],
            )
        )

    # Legacy alias no longer needed; UseCase defined above

    def validate_bundle_integrity(self) -> dict[str, Any]:
        issues: list[str] = []
        ids = [getattr(e.resource, "id", None) for e in self.entries if e.resource is not None]
        if len(ids) != len(set(ids)):
            issues.append("Duplicate resource IDs found in bundle")
        # Unique workflow ids
        wf_ids = [getattr(w, "workflow_id", None) for w in self.workflow_bindings]
        if len(wf_ids) != len(set(wf_ids)):
            issues.append("Workflow bindings must have unique workflow_ids")
        if self.bundle_type in (BundleType.STACK, BundleType.TEMPLATE) and len(self.entries) == 0:
            raise ValueError("stack bundles must contain at least one entry")
        # Enforce non-empty for STACK/TEMPLATE at integrity check time
        return {
            "valid": len(issues) == 0,
            "entry_count": len(self.entries),
            "workflow_binding_count": len(self.workflow_bindings),
            "use_case_count": len(self.use_cases),
            "issues": issues,
        }

    # Validation rules expected by tests
    @model_validator(mode="after")
    def _validate_constraints(self):  # type: ignore[override]
        if self.total is not None and self.bundle_type != BundleType.SEARCHSET:
            raise ValueError("total field is only valid for searchset bundles")
        # Allow empty STACK/TEMPLATE at init; tests construct then mutate.
        if self.bundle_type == BundleType.DOCUMENT and len(self.entries) == 0:
            raise ValueError("document bundles must contain at least one entry")
        # ensure workflow ids unique
        wf_ids = [getattr(w, "workflow_id", None) for w in self.workflow_bindings]
        if len(wf_ids) != len(set(wf_ids)):
            raise ValueError("Workflow bindings must have unique workflow_ids")
        return self

    def add_update_record(
        self,
        version: str,
        summary: str,
        author: str | None = None,
        details: str | None = None,
        breaking_changes: bool = False,
        migration_notes: str | None = None,
    ) -> None:
        self.updates.append(
            type(
                "_Update",
                (),
                {
                    "version": version,
                    "summary": summary,
                    "author": author,
                    "details": details,
                    "breaking_changes": breaking_changes,
                    "migration_notes": migration_notes,
                },
            )()
        )

    # Provide a class alias for tests importing BundleUpdate
    class BundleUpdate(BaseResource):  # pragma: no cover
        resource_type: Literal["BundleUpdate"] = Field(default="BundleUpdate")
        version: str
        summary: str
        author: str | None = None
        details: str | None = None
        breaking_changes: bool = False
        migration_notes: str | None = None
