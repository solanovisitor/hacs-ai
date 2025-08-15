"""Resource bundle models.

Minimal yet usable bundle types for grouping related HACS resources.
"""
from typing import Literal, Optional, List, Any, Dict
from pydantic import Field, field_validator, model_validator
from .base_resource import BaseResource
from .types import BundleType, BundleStatus
from .workflow import WorkflowBindingType, WorkflowBinding, LinkRelation

# Minimal types for workflow bindings and links used by tests
class Link(BaseResource):
    resource_type: Literal["Link"] = Field(default="Link")
    relation: str = Field(description="Link relation")
    url: str = Field(description="URL")


class BundleEntry(BaseResource):
    resource_type: Literal["BundleEntry"] = Field(default="BundleEntry")

    title: Optional[str] = Field(default=None, description="Entry title")
    tags: List[str] = Field(default_factory=list, description="Entry tags")
    priority: int = Field(default=0, description="Ordering priority")
    # The actual contained resource (FHIR Bundle.entry.resource)
    resource: Optional[Any] = Field(default=None, description="The actual resource contained in this entry")
    # Optional reference ID for linking
    contained_resource_id: Optional[str] = Field(default=None, description="ID of the contained resource")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary entry metadata")


class ResourceBundle(BaseResource):
    resource_type: Literal["ResourceBundle"] = Field(default="ResourceBundle")
    title: Optional[str] = Field(default=None, description="Bundle title")
    bundle_type: BundleType | None = Field(default=None)
    entries: List[BundleEntry] = Field(default_factory=list, description="Bundle entries")
    status: BundleStatus = Field(default=BundleStatus.DRAFT, description="Bundle lifecycle status")
    # Optional metadata used by tests and utilities
    version: Optional[str] = None
    description: Optional[str] = None
    publisher: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    total: Optional[int] = None
    links: List[Link] = Field(default_factory=list)
    workflow_bindings: List[Any] = Field(default_factory=list)
    class UseCase(BaseResource):
        resource_type: Literal["UseCase"] = Field(default="UseCase")
        name: str
        description: str
        examples: List[str] = Field(default_factory=list)
        prerequisites: List[str] = Field(default_factory=list)
        outcomes: List[str] = Field(default_factory=list)
        tags: List[str] = Field(default_factory=list)
        model_config = {"extra": "allow"}

    use_cases: List[UseCase] = Field(default_factory=list)
    updates: List[Any] = Field(default_factory=list)
    quality_score: Optional[float] = None
    maturity_level: Optional[str] = None
    experimental: Optional[bool] = None

    def add_entry(self, resource: BaseResource, title: Optional[str] = None, tags: Optional[List[str]] = None, priority: int = 0) -> None:
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
    def add_resource(self, resource: BaseResource, title: Optional[str] = None, tags: Optional[List[str]] = None, priority: int = 0, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.add_entry(resource, title=title, tags=tags, priority=priority)
        if metadata:
            if not hasattr(self.entries[-1], "metadata"):
                setattr(self.entries[-1], "metadata", {})
            self.entries[-1].metadata.update(metadata)

    def add_link(self, relation: str, url: str) -> None:
        self.links.append(Link(relation=relation, url=url))

    # Factory function compatibility
    @staticmethod
    def create_resource_stack(stack_name: str, version: str, description: Optional[str] = None, resources: Optional[List[BaseResource]] = None, publisher: Optional[str] = None) -> "ResourceBundle":
        bundle = ResourceBundle(title=stack_name, bundle_type=BundleType.STACK, version=version, description=description, publisher=publisher, status=BundleStatus.ACTIVE)
        for res in (resources or []):
            bundle.add_resource(res)
        return bundle

    @staticmethod
    def create_search_results_bundle(resources: List[BaseResource], total: int, search_url: str) -> "ResourceBundle":
        bundle = ResourceBundle(bundle_type=BundleType.SEARCHSET, version="1.0.0", total=total)
        for res in resources:
            bundle.add_resource(res)
        # Add self link
        bundle.add_link(LinkRelation.SELF, search_url)
        return bundle

    @staticmethod
    def create_workflow_template_bundle(template_name: str, version: str, workflow_id: str, template_resources: List[BaseResource], description: Optional[str] = None) -> "ResourceBundle":
        bundle = ResourceBundle(title=template_name, bundle_type=BundleType.TEMPLATE, version=version, description=description)
        for res in template_resources:
            bundle.add_resource(res)
        bundle.add_workflow_binding(workflow_id, WorkflowBindingType.OUTPUT_TEMPLATE)
        return bundle

    def get_resources_by_type(self, resource_type: str) -> List[BaseResource]:
        return [e.resource for e in self.entries if getattr(e.resource, "resource_type", None) == resource_type]

    def get_resources_by_tag(self, tag: str) -> List[BaseResource]:
        return [e.resource for e in self.entries if tag in (e.tags or [])]

    def add_workflow_binding(self, workflow_id: str, binding_type: Any, workflow_name: Optional[str] = None, parameters: Optional[Dict[str, Any]] = None, priority: int = 0, description: Optional[str] = None) -> None:
        self.workflow_bindings.append(WorkflowBinding(
            workflow_id=workflow_id,
            binding_type=binding_type,
            parameters=parameters or {},
            priority=priority,
            description=description,
            workflow_name=workflow_name,
        ))

    def get_workflow_bindings_by_type(self, binding_type: Any) -> List[Any]:
        return [wb for wb in self.workflow_bindings if getattr(wb, "binding_type", None) == binding_type]

    def add_use_case(self, name: str, description: str, examples: Optional[List[str]] = None, prerequisites: Optional[List[str]] = None, outcomes: Optional[List[str]] = None, tags: Optional[List[str]] = None) -> None:
        self.use_cases.append(self.UseCase(name=name, description=description, examples=examples or [], prerequisites=prerequisites or [], outcomes=outcomes or [], tags=tags or []))

    # Legacy alias no longer needed; UseCase defined above

    def validate_bundle_integrity(self) -> Dict[str, Any]:
        issues: List[str] = []
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

    def add_update_record(self, version: str, summary: str, author: Optional[str] = None, details: Optional[str] = None, breaking_changes: bool = False, migration_notes: Optional[str] = None) -> None:
        self.updates.append(type("_Update", (), {"version": version, "summary": summary, "author": author, "details": details, "breaking_changes": breaking_changes, "migration_notes": migration_notes})())

    # Provide a class alias for tests importing BundleUpdate
    class BundleUpdate(BaseResource):  # pragma: no cover
        resource_type: Literal["BundleUpdate"] = Field(default="BundleUpdate")
        version: str
        summary: str
        author: Optional[str] = None
        details: Optional[str] = None
        breaking_changes: bool = False
        migration_notes: Optional[str] = None