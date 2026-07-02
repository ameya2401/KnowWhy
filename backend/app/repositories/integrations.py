from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.integration import (
    Commit,
    Integration,
    Issue,
    PullRequest,
)
from app.models.integration import (
    IntegrationRepository as IntegrationRepositoryModel,
)


class IntegrationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, integration: Integration) -> Integration:
        self.session.add(integration)
        await self.session.flush()
        return integration

    async def get_by_id(self, integration_id: UUID) -> Integration | None:
        result = await self.session.execute(
            select(Integration)
            .options(selectinload(Integration.repositories))
            .where(Integration.id == integration_id)
        )
        return result.scalar_one_or_none()

    async def get_by_project_and_provider(
        self, project_id: UUID, provider: str
    ) -> Integration | None:
        result = await self.session.execute(
            select(Integration)
            .options(selectinload(Integration.repositories))
            .where(
                Integration.project_id == project_id,
                Integration.provider == provider,
            )
        )
        return result.scalar_one_or_none()

    async def delete(self, integration: Integration) -> None:
        await self.session.delete(integration)


class IntegrationRepositoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, repo: IntegrationRepositoryModel) -> IntegrationRepositoryModel:
        self.session.add(repo)
        await self.session.flush()
        return repo

    async def get_by_id(self, repo_id: UUID) -> IntegrationRepositoryModel | None:
        result = await self.session.execute(
            select(IntegrationRepositoryModel).where(IntegrationRepositoryModel.id == repo_id)
        )
        return result.scalar_one_or_none()

    async def get_by_integration_and_github_id(
        self, integration_id: UUID, github_repo_id: str
    ) -> IntegrationRepositoryModel | None:
        result = await self.session.execute(
            select(IntegrationRepositoryModel).where(
                IntegrationRepositoryModel.integration_id == integration_id,
                IntegrationRepositoryModel.github_repo_id == github_repo_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_integration(self, integration_id: UUID) -> list[IntegrationRepositoryModel]:
        result = await self.session.execute(
            select(IntegrationRepositoryModel)
            .where(IntegrationRepositoryModel.integration_id == integration_id)
            .order_by(IntegrationRepositoryModel.name.asc())
        )
        return list(result.scalars().all())

    async def delete(self, repo: IntegrationRepositoryModel) -> None:
        await self.session.delete(repo)


class SyncDataRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_commit(self, commit: Commit) -> Commit:
        self.session.add(commit)
        await self.session.flush()
        return commit

    async def get_commit_by_sha(self, repository_id: UUID, sha: str) -> Commit | None:
        result = await self.session.execute(
            select(Commit).where(
                Commit.repository_id == repository_id,
                Commit.sha == sha,
            )
        )
        return result.scalar_one_or_none()

    async def create_pull_request(self, pr: PullRequest) -> PullRequest:
        self.session.add(pr)
        await self.session.flush()
        return pr

    async def get_pull_request_by_github_id(
        self, repository_id: UUID, github_pr_id: str
    ) -> PullRequest | None:
        result = await self.session.execute(
            select(PullRequest).where(
                PullRequest.repository_id == repository_id,
                PullRequest.github_pr_id == github_pr_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_issue(self, issue: Issue) -> Issue:
        self.session.add(issue)
        await self.session.flush()
        return issue

    async def get_issue_by_github_id(
        self, repository_id: UUID, github_issue_id: str
    ) -> Issue | None:
        result = await self.session.execute(
            select(Issue).where(
                Issue.repository_id == repository_id,
                Issue.github_issue_id == github_issue_id,
            )
        )
        return result.scalar_one_or_none()
