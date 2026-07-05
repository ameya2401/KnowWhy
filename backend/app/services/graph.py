from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ai_chat import AIConversation
from app.models.integration import Integration, IntegrationRepository
from app.models.knowledge import KnowledgeItem, KnowledgeRelationship
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.schemas.graph import (
    EntityDetailResponse,
    EntityRelationshipDetail,
    GraphEdge,
    GraphNode,
    GraphResponse,
    NeighborInfo,
    TimelineEvent,
    TimelineResponse,
)


class GraphService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_project_graph(
        self,
        project_id: UUID,
        limit: int = 500,
        offset: int = 0,
        entity_types: list[str] | None = None,
    ) -> GraphResponse:
        """
        Builds and returns the knowledge graph for a project.
        Fetches the Project itself, User members, Integrations, connected Repos, 
        KnowledgeItems, and KnowledgeRelationships, connecting them with explicit and implicit edges.
        """  # noqa: E501
        nodes = []
        edges = []

        # 1. Fetch Project
        project_stmt = select(Project).where(Project.id == project_id)
        project_res = await self.session.execute(project_stmt)
        project = project_res.scalar_one_or_none()
        if not project:
            return GraphResponse(nodes=[], edges=[])

        # Add Project Node
        project_node_id = f"project-{project.id}"
        if not entity_types or "project" in entity_types:
            nodes.append(
                GraphNode(
                    id=project_node_id,
                    type="project",
                    title=project.name,
                    subtitle=project.slug,
                    url=None,
                    author=None,
                    metadata={"description": project.description or ""},
                )
            )

        # 2. Fetch Project Members (Users)
        members_stmt = (
            select(User)
            .join(ProjectMember, ProjectMember.user_id == User.id)
            .where(ProjectMember.project_id == project_id)
        )
        members_res = await self.session.execute(members_stmt)
        members = members_res.scalars().all()
        for member in members:
            member_node_id = f"user-{member.id}"
            if not entity_types or "user" in entity_types:
                nodes.append(
                    GraphNode(
                        id=member_node_id,
                        type="user",
                        title=member.full_name or member.email,
                        subtitle=member.email,
                        url=None,
                        author=None,
                        metadata={"email": member.email},
                    )
                )
            # Edge: Project -> has_member -> User
            if not entity_types or ("project" in entity_types and "user" in entity_types):
                edges.append(
                    GraphEdge(
                        id=f"edge-proj-member-{member.id}",
                        source=project_node_id,
                        target=member_node_id,
                        type="contains",
                        confidence=1.0,
                        metadata={"role": "member"},
                    )
                )

        # 3. Fetch Integrations
        integrations_stmt = select(Integration).where(Integration.project_id == project_id)
        integrations_res = await self.session.execute(integrations_stmt)
        integrations = integrations_res.scalars().all()
        for integration in integrations:
            int_node_id = f"integration-{integration.id}"
            if not entity_types or "integration" in entity_types:
                nodes.append(
                    GraphNode(
                        id=int_node_id,
                        type="integration",
                        title=f"{integration.provider.value.title()} Integration",
                        subtitle=integration.status.value,
                        url=None,
                        author=None,
                        metadata={
                            "provider": integration.provider.value,
                            "status": integration.status.value,
                            "workspace_name": integration.workspace_name or "",
                        },
                    )
                )
            # Edge: Project -> contains -> Integration
            if not entity_types or ("project" in entity_types and "integration" in entity_types):
                edges.append(
                    GraphEdge(
                        id=f"edge-proj-int-{integration.id}",
                        source=project_node_id,
                        target=int_node_id,
                        type="contains",
                        confidence=1.0,
                    )
                )

            # 4. Fetch Repositories if GitHub Integration
            if integration.provider.value == "github":
                repos_stmt = select(IntegrationRepository).where(
                    IntegrationRepository.integration_id == integration.id
                )
                repos_res = await self.session.execute(repos_stmt)
                repos = repos_res.scalars().all()
                for repo in repos:
                    repo_node_id = f"repo-{repo.id}"
                    if not entity_types or "repository" in entity_types:
                        nodes.append(
                            GraphNode(
                                id=repo_node_id,
                                type="repository",
                                title=repo.name,
                                subtitle=f"{repo.owner}/{repo.name}",
                                url=repo.clone_url,
                                author=repo.owner,
                                metadata={
                                    "default_branch": repo.default_branch,
                                    "visibility": repo.visibility,
                                },
                            )
                        )
                    # Edge: Integration -> contains -> Repository
                    if not entity_types or ("integration" in entity_types and "repository" in entity_types):  # noqa: E501
                        edges.append(
                            GraphEdge(
                                id=f"edge-int-repo-{repo.id}",
                                source=int_node_id,
                                target=repo_node_id,
                                type="contains",
                                confidence=1.0,
                            )
                        )

        # 5. Fetch KnowledgeItems
        items_stmt = (
            select(KnowledgeItem)
            .where(KnowledgeItem.project_id == project_id)
            .limit(limit)
            .offset(offset)
        )
        if entity_types:
            # Map entity types back to what's stored in knowledge items
            kb_types = [t for t in entity_types if t not in ["project", "user", "integration", "repository"]]  # noqa: E501
            if kb_types:
                items_stmt = items_stmt.where(KnowledgeItem.entity_type.in_(kb_types))
            else:
                # If only virtual node types were requested, skip querying database knowledge items
                items_stmt = None

        kb_items = []
        if items_stmt is not None:
            items_res = await self.session.execute(items_stmt)
            kb_items = items_res.scalars().all()

        kb_item_ids = {item.id for item in kb_items}
        for item in kb_items:
            item_node_id = str(item.id)
            nodes.append(
                GraphNode(
                    id=item_node_id,
                    type=item.entity_type,
                    title=item.title,
                    subtitle=item.source,
                    url=item.url,
                    author=item.author,
                    metadata={
                        "source": item.source,
                        "entity_type": item.entity_type,
                        "created_time": item.created_time.isoformat(),
                        "updated_time": item.updated_time.isoformat(),
                        "tags": item.tags or [],
                    },
                )
            )

            # Implicit Edges:
            # Connect commit/PR/issue to Repository if we have a match
            if item.source == "github":
                # Find matching repository name from metadata or URL
                # By default connect to project's first Repository node or parse repo owner
                # Since we don't have explicit repository foreign key on KnowledgeItem directly,
                # we can connect it to the Project node or to Repository node if repos are found
                for node in nodes:
                    if node.type == "repository":
                        edges.append(
                            GraphEdge(
                                id=f"edge-repo-item-{item.id}",
                                source=node.id,
                                target=item_node_id,
                                type="contains",
                                confidence=1.0,
                            )
                        )
                        break
                else:
                    edges.append(
                        GraphEdge(
                            id=f"edge-proj-item-{item.id}",
                            source=project_node_id,
                            target=item_node_id,
                            type="contains",
                            confidence=1.0,
                        )
                    )
            else:
                # Notion/Drive connect to Project or parent Notion Page/Drive Folder (contains)
                edges.append(
                    GraphEdge(
                        id=f"edge-proj-item-{item.id}",
                        source=project_node_id,
                        target=item_node_id,
                        type="contains",
                        confidence=1.0,
                    )
                )

            # User author association
            if item.author:
                for node in nodes:
                    if node.type == "user" and (
                        node.title.lower() in item.author.lower()
                        or item.author.lower() in node.title.lower()
                    ):
                        edges.append(
                            GraphEdge(
                                id=f"edge-user-created-{node.id}-{item.id}",
                                source=node.id,
                                target=item_node_id,
                                type="created",
                                confidence=0.8,
                            )
                        )
                        break

        # 6. Fetch KnowledgeRelationships between the retrieved KnowledgeItems
        if kb_item_ids:
            rel_stmt = select(KnowledgeRelationship).where(
                and_(
                    KnowledgeRelationship.source_item_id.in_(kb_item_ids),
                    KnowledgeRelationship.target_item_id.in_(kb_item_ids),
                )
            )
            rel_res = await self.session.execute(rel_stmt)
            relationships = rel_res.scalars().all()
            for rel in relationships:
                edges.append(
                    GraphEdge(
                        id=str(rel.id),
                        source=str(rel.source_item_id),
                        target=str(rel.target_item_id),
                        type=rel.relationship_type,
                        confidence=rel.confidence,
                        metadata=rel.metadata_json or {},
                    )
                )

        return GraphResponse(nodes=nodes, edges=edges)

    async def get_entity_detail(self, entity_id: str, project_id: UUID) -> EntityDetailResponse:
        """
        Retrieves complete properties of a graph entity (either KnowledgeItem or virtual node),
        along with all direct incoming/outgoing relationships.
        """
        # Check if UUID
        is_uuid = False
        try:
            uuid_val = UUID(entity_id)
            is_uuid = True
        except ValueError:
            pass

        node = None
        relationships = []

        if is_uuid:
            # 1. Fetch KnowledgeItem
            item_stmt = select(KnowledgeItem).where(
                and_(KnowledgeItem.id == uuid_val, KnowledgeItem.project_id == project_id)
            )
            item_res = await self.session.execute(item_stmt)
            item = item_res.scalar_one_or_none()
            if item:
                node = GraphNode(
                    id=str(item.id),
                    type=item.entity_type,
                    title=item.title,
                    subtitle=item.source,
                    url=item.url,
                    author=item.author,
                    metadata={
                        "description": item.description or "",
                        "content": item.content or "",
                        "source": item.source,
                        "entity_type": item.entity_type,
                        "created_time": item.created_time.isoformat(),
                        "updated_time": item.updated_time.isoformat(),
                        "tags": item.tags or [],
                        "metadata_json": item.metadata_json or {},
                    },
                )

                # Fetch outgoing relationships
                out_stmt = (
                    select(KnowledgeRelationship)
                    .options(selectinload(KnowledgeRelationship.target_item))
                    .where(KnowledgeRelationship.source_item_id == item.id)
                )
                out_res = await self.session.execute(out_stmt)
                for rel in out_res.scalars().all():
                    if rel.target_item:
                        relationships.append(
                            EntityRelationshipDetail(
                                neighbor=NeighborInfo(
                                    id=str(rel.target_item.id),
                                    type=rel.target_item.entity_type,
                                    title=rel.target_item.title,
                                ),
                                edge_type=rel.relationship_type,
                                direction="outgoing",
                                confidence=rel.confidence,
                                metadata=rel.metadata_json,
                            )
                        )

                # Fetch incoming relationships
                in_stmt = (
                    select(KnowledgeRelationship)
                    .options(selectinload(KnowledgeRelationship.source_item))
                    .where(KnowledgeRelationship.target_item_id == item.id)
                )
                in_res = await self.session.execute(in_stmt)
                for rel in in_res.scalars().all():
                    if rel.source_item:
                        relationships.append(
                            EntityRelationshipDetail(
                                neighbor=NeighborInfo(
                                    id=str(rel.source_item.id),
                                    type=rel.source_item.entity_type,
                                    title=rel.source_item.title,
                                ),
                                edge_type=rel.relationship_type,
                                direction="incoming",
                                confidence=rel.confidence,
                                metadata=rel.metadata_json,
                            )
                        )

        # 2. Virtual nodes handling
        if not node:
            # Project check
            if entity_id.startswith("project-"):
                proj_id_str = entity_id.replace("project-", "")
                if proj_id_str == str(project_id):
                    proj_stmt = select(Project).where(Project.id == project_id)
                    proj_res = await self.session.execute(proj_stmt)
                    proj = proj_res.scalar_one_or_none()
                    if proj:
                        node = GraphNode(
                            id=entity_id,
                            type="project",
                            title=proj.name,
                            subtitle=proj.slug,
                            metadata={
                                "description": proj.description or "",
                                "status": proj.status.value,
                                "visibility": proj.visibility.value,
                            },
                        )
            # User check
            elif entity_id.startswith("user-"):
                user_id_str = entity_id.replace("user-", "")
                user_stmt = (
                    select(User)
                    .join(ProjectMember, ProjectMember.user_id == User.id)
                    .where(and_(ProjectMember.project_id == project_id, User.id == UUID(user_id_str)))  # noqa: E501
                )
                user_res = await self.session.execute(user_stmt)
                user = user_res.scalar_one_or_none()
                if user:
                    node = GraphNode(
                        id=entity_id,
                        type="user",
                        title=user.full_name or user.email,
                        subtitle=user.email,
                        metadata={
                            "email": user.email,
                            "is_active": user.is_active,
                        },
                    )
            # Integration check
            elif entity_id.startswith("integration-"):
                int_id_str = entity_id.replace("integration-", "")
                int_stmt = select(Integration).where(
                    and_(Integration.project_id == project_id, Integration.id == UUID(int_id_str))
                )
                int_res = await self.session.execute(int_stmt)
                integration = int_res.scalar_one_or_none()
                if integration:
                    node = GraphNode(
                        id=entity_id,
                        type="integration",
                        title=f"{integration.provider.value.title()} Integration",
                        subtitle=integration.status.value,
                        metadata={
                            "provider": integration.provider.value,
                            "status": integration.status.value,
                            "workspace_name": integration.workspace_name or "",
                        },
                    )

        if not node:
            raise ValueError("Entity not found or access denied.")

        return EntityDetailResponse(entity=node, relationships=relationships)

    async def get_project_timeline(
        self,
        project_id: UUID,
        entity_type: str | None = None,
        source: str | None = None,
        author: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> TimelineResponse:
        """
        Generates a chronological timeline of events for a project.
        Includes commits, PRs, issues, documentation updates, and optionally AI conversations.
        """
        events = []

        # 1. Query KnowledgeItems
        items_stmt = select(KnowledgeItem).where(KnowledgeItem.project_id == project_id)
        if entity_type:
            items_stmt = items_stmt.where(KnowledgeItem.entity_type == entity_type)
        if source:
            items_stmt = items_stmt.where(KnowledgeItem.source == source)
        if author:
            items_stmt = items_stmt.where(KnowledgeItem.author.ilike(f"%{author}%"))
        if start_date:
            items_stmt = items_stmt.where(KnowledgeItem.created_time >= start_date)
        if end_date:
            items_stmt = items_stmt.where(KnowledgeItem.created_time <= end_date)

        # Order by created_time descending
        items_stmt = items_stmt.order_by(KnowledgeItem.created_time.desc()).limit(limit).offset(offset)  # noqa: E501
        items_res = await self.session.execute(items_stmt)
        items = items_res.scalars().all()

        for item in items:
            events.append(
                TimelineEvent(
                    id=str(item.id),
                    type=item.entity_type,
                    title=item.title,
                    description=item.description,
                    time=item.created_time,
                    author=item.author,
                    url=item.url,
                    metadata={
                        "source": item.source,
                        "updated_time": item.updated_time.isoformat(),
                    },
                )
            )

        # 2. Add AI Conversations as events if not filtered out
        if not entity_type or entity_type == "ai_conversation":
            conv_stmt = select(AIConversation).where(AIConversation.project_id == project_id)
            if start_date:
                conv_stmt = conv_stmt.where(AIConversation.created_at >= start_date)
            if end_date:
                conv_stmt = conv_stmt.where(AIConversation.created_at <= end_date)

            conv_stmt = conv_stmt.order_by(AIConversation.created_at.desc()).limit(limit)
            conv_res = await self.session.execute(conv_stmt)
            conversations = conv_res.scalars().all()

            for conv in conversations:
                events.append(
                    TimelineEvent(
                        id=str(conv.id),
                        type="ai_conversation",
                        title=conv.title,
                        description=f"AI Conversation session with {conv.provider} (temp: {conv.temperature})",  # noqa: E501
                        time=conv.created_at,
                        author="AI Assistant",
                        url=None,
                        metadata={
                            "provider": conv.provider,
                            "model": conv.model,
                            "citation_mode": conv.citation_mode,
                        },
                    )
                )

        # Re-sort all events chronologically descending
        events.sort(key=lambda x: x.time, reverse=True)

        # Apply pagination limit to the merged list
        events = events[offset : offset + limit]

        return TimelineResponse(events=events)
