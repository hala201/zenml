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
"""SQL Model Implementations for Actions."""

import base64
import json
from typing import TYPE_CHECKING, Any, List, Optional, Sequence
from uuid import UUID

from pydantic.json import pydantic_encoder
from sqlalchemy import TEXT, Column, UniqueConstraint
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.base import ExecutableOption
from sqlmodel import Field, Relationship

from zenml.models import (
    ActionRequest,
    ActionResponse,
    ActionResponseBody,
    ActionResponseMetadata,
    ActionResponseResources,
    ActionUpdate,
)
from zenml.utils.time_utils import utc_now
from zenml.zen_stores.schemas.base_schemas import NamedSchema
from zenml.zen_stores.schemas.project_schemas import ProjectSchema
from zenml.zen_stores.schemas.schema_utils import build_foreign_key_field
from zenml.zen_stores.schemas.user_schemas import UserSchema
from zenml.zen_stores.schemas.utils import jl_arg

if TYPE_CHECKING:
    from zenml.zen_stores.schemas import TriggerSchema


class ActionSchema(NamedSchema, table=True):
    """SQL Model for actions."""

    __tablename__ = "action"
    __table_args__ = (
        UniqueConstraint(
            "name",
            "project_id",
            name="unique_action_name_in_project",
        ),
    )

    project_id: UUID = build_foreign_key_field(
        source=__tablename__,
        target=ProjectSchema.__tablename__,
        source_column="project_id",
        target_column="id",
        ondelete="CASCADE",
        nullable=False,
    )
    project: "ProjectSchema" = Relationship(back_populates="actions")

    user_id: Optional[UUID] = build_foreign_key_field(
        source=__tablename__,
        target=UserSchema.__tablename__,
        source_column="user_id",
        target_column="id",
        ondelete="SET NULL",
        nullable=True,
    )
    user: Optional["UserSchema"] = Relationship(
        back_populates="actions",
        sa_relationship_kwargs={"foreign_keys": "[ActionSchema.user_id]"},
    )

    triggers: List["TriggerSchema"] = Relationship(back_populates="action")

    service_account_id: UUID = build_foreign_key_field(
        source=__tablename__,
        target=UserSchema.__tablename__,
        source_column="service_account_id",
        target_column="id",
        ondelete="CASCADE",
        nullable=False,
    )
    service_account: UserSchema = Relationship(
        back_populates="auth_actions",
        sa_relationship_kwargs={
            "foreign_keys": "[ActionSchema.service_account_id]"
        },
    )
    auth_window: int

    flavor: str = Field(nullable=False)
    plugin_subtype: str = Field(nullable=False)
    description: Optional[str] = Field(sa_column=Column(TEXT, nullable=True))

    configuration: bytes

    @classmethod
    def get_query_options(
        cls,
        include_metadata: bool = False,
        include_resources: bool = False,
        **kwargs: Any,
    ) -> Sequence[ExecutableOption]:
        """Get the query options for the schema.

        Args:
            include_metadata: Whether metadata will be included when converting
                the schema to a model.
            include_resources: Whether resources will be included when
                converting the schema to a model.
            **kwargs: Keyword arguments to allow schema specific logic

        Returns:
            A list of query options.
        """
        options = []

        if include_resources:
            options.extend(
                [
                    joinedload(jl_arg(ActionSchema.user)),
                    joinedload(
                        jl_arg(ActionSchema.service_account), innerjoin=True
                    ),
                ]
            )

        return options

    @classmethod
    def from_request(cls, request: "ActionRequest") -> "ActionSchema":
        """Convert a `ActionRequest` to a `ActionSchema`.

        Args:
            request: The request model to convert.

        Returns:
            The converted schema.
        """
        return cls(
            name=request.name,
            project_id=request.project,
            user_id=request.user,
            configuration=base64.b64encode(
                json.dumps(
                    request.configuration, default=pydantic_encoder
                ).encode("utf-8"),
            ),
            flavor=request.flavor,
            plugin_subtype=request.plugin_subtype,
            description=request.description,
            service_account_id=request.service_account_id,
            auth_window=request.auth_window,
        )

    def update(self, action_update: "ActionUpdate") -> "ActionSchema":
        """Updates a action schema with a action update model.

        Args:
            action_update: `ActionUpdate` to update the action with.

        Returns:
            The updated ActionSchema.
        """
        for field, value in action_update.dict(
            exclude_unset=True,
            exclude_none=True,
        ).items():
            if field == "configuration":
                self.configuration = base64.b64encode(
                    json.dumps(
                        action_update.configuration, default=pydantic_encoder
                    ).encode("utf-8")
                )
            else:
                setattr(self, field, value)

        self.updated = utc_now()
        return self

    def to_model(
        self,
        include_metadata: bool = False,
        include_resources: bool = False,
        **kwargs: Any,
    ) -> "ActionResponse":
        """Converts the action schema to a model.

        Args:
            include_metadata: Flag deciding whether to include the output model(s)
                metadata fields in the response.
            include_resources: Flag deciding whether to include the output model(s)
                metadata fields in the response.
            **kwargs: Keyword arguments to allow schema specific logic

        Returns:
            The converted model.
        """
        body = ActionResponseBody(
            user_id=self.user_id,
            project_id=self.project_id,
            created=self.created,
            updated=self.updated,
            flavor=self.flavor,
            plugin_subtype=self.plugin_subtype,
        )
        metadata = None
        if include_metadata:
            metadata = ActionResponseMetadata(
                configuration=json.loads(
                    base64.b64decode(self.configuration).decode()
                ),
                description=self.description,
                auth_window=self.auth_window,
            )
        resources = None
        if include_resources:
            resources = ActionResponseResources(
                user=self.user.to_model() if self.user else None,
                service_account=self.service_account.to_model(),
            )
        return ActionResponse(
            id=self.id,
            name=self.name,
            body=body,
            metadata=metadata,
            resources=resources,
        )
