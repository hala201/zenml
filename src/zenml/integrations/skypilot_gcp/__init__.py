#  Copyright (c) ZenML GmbH 2024. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.
"""Initialization of the Skypilot GCP integration for ZenML.

The Skypilot integration sub-module powers an alternative to the local
orchestrator for a remote orchestration of ZenML pipelines on VMs.
"""
from typing import List, Type

from zenml.integrations.constants import (
    SKYPILOT_GCP,
)
from zenml.integrations.integration import Integration
from zenml.stack import Flavor

SKYPILOT_GCP_ORCHESTRATOR_FLAVOR = "vm_gcp"


class SkypilotGCPIntegration(Integration):
    """Definition of Skypilot (GCP) Integration for ZenML."""

    NAME = SKYPILOT_GCP
    REQUIREMENTS = [
        "skypilot[gcp]==0.9.3",
        # TODO: Remove this once the issue is fixed:
        # Adding the dependencies of the GCP integration on top of the
        # requirements of the skypilot integration results in a
        # very long resolution time for pip. This is a workaround to
        # speed up the resolution.
        "protobuf>=4.25.0,<5.0.0",
    ]
    APT_PACKAGES = ["openssh-client", "rsync"]

    @classmethod
    def flavors(cls) -> List[Type[Flavor]]:
        """Declare the stack component flavors for the Skypilot GCP integration.

        Returns:
            List of stack component flavors for this integration.
        """
        from zenml.integrations.skypilot_gcp.flavors import (
            SkypilotGCPOrchestratorFlavor,
        )

        return [SkypilotGCPOrchestratorFlavor]
