"""Resource bundle models.

Minimal yet usable bundle types for grouping related HACS resources.
"""
from typing import Literal, Optional, List, Any
from pydantic import Field
from .base_resource import BaseResource
from .types import BundleType


class BundleEntry(BaseResource):
    resource_type: Literal["BundleEntry"] = Field(default="BundleEntry")

    title: Optional[str] = Field(default=None, description="Entry title")
    tags: List[str] = Field(default_factory=list, description="Entry tags")
    priority: int = Field(default=0, description="Ordering priority")
    # The actual contained resource (FHIR Bundle.entry.resource)
    resource: Optional[Any] = Field(default=None, description="The actual resource contained in this entry")
    # Optional reference ID for linking
    contained_resource_id: Optional[str] = Field(default=None, description="ID of the contained resource")


class ResourceBundle(BaseResource):
    resource_type: Literal["ResourceBundle"] = Field(default="ResourceBundle")
    title: Optional[str] = Field(default=None, description="Bundle title")
    bundle_type: BundleType | None = Field(default=None)
    entries: List[BundleEntry] = Field(default_factory=list, description="Bundle entries")

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