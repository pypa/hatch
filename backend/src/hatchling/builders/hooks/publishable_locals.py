import os
from typing import Optional

from packaging.requirements import Requirement

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from hatchling.metadata.core import ProjectMetadata


class PublishableLocalsHook(BuildHookInterface):
    PLUGIN_NAME = 'publishable_locals'

    def local_dependency_path(self, req: Requirement) -> Optional[str]:
        if not req.url:
            return None
        req_url = req.url
        if req_url.startswith("file://"):
            req_url = req.url[len("file://"):]
        elif ":" in req_url:
            return None
        if req_url.startswith("/"):
            p_path = req_url
        else:
            p_path = os.path.normpath(os.path.join(self.root, req_url))
        return p_path if os.path.isdir(p_path) else None

    def publishable_local(self, req: Requirement) -> Requirement:
        p_path = self.local_dependency_path(req)
        if p_path:
            p_meta = ProjectMetadata(p_path, plugin_manager=self.metadata.plugin_manager)
            p_ver = p_meta.version
            return Requirement(f"{req.name}=={p_ver}")
        else:
            return req
