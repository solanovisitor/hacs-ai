"""Resource bundle models - placeholder for now."""
from typing import Literal
from pydantic import Field
from .base_resource import BaseResource
from .types import BundleType

class BundleEntry(BaseResource):
    resource_type: Literal["BundleEntry"] = Field(default="BundleEntry")

class ResourceBundle(BaseResource):
    resource_type: Literal["ResourceBundle"] = Field(default="ResourceBundle")
    bundle_type: BundleType | None = Field(default=None)