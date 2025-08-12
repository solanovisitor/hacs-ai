"""Resource bundle models.

Minimal yet usable bundle types for grouping related HACS resources.
"""
from typing import Literal, Optional, List
from pydantic import Field
from .base_resource import BaseResource
from .types import BundleType


class BundleEntry(BaseResource):
    resource_type: Literal["BundleEntry"] = Field(default="BundleEntry")

    title: Optional[str] = Field(default=None, description="Entry title")
    tags: List[str] = Field(default_factory=list, description="Entry tags")
    priority: int = Field(default=0, description="Ordering priority")
    # A reference to the contained resource (by id or inline id)
    contained_resource_id: Optional[str] = Field(default=None, description="ID of the contained resource")


class ResourceBundle(BaseResource):
    resource_type: Literal["ResourceBundle"] = Field(default="ResourceBundle")
    title: Optional[str] = Field(default=None, description="Bundle title")
    bundle_type: BundleType | None = Field(default=None)
    entries: List[BundleEntry] = Field(default_factory=list, description="Bundle entries")