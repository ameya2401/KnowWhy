from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

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

    async def get_stats(self, repo_ids: list[UUID]) -> dict:
        if not repo_ids:
            return {"total_commits": 0, "pull_requests": 0, "open_issues": 0, "contributors": 0}

        commits_count = (
            await self.session.scalar(
                select(func.count(Commit.id)).where(Commit.repository_id.in_(repo_ids))
            )
            or 0
        )

        prs_count = (
            await self.session.scalar(
                select(func.count(PullRequest.id)).where(PullRequest.repository_id.in_(repo_ids))
            )
            or 0
        )

        open_issues_count = (
            await self.session.scalar(
                select(func.count(Issue.id)).where(
                    Issue.repository_id.in_(repo_ids), Issue.state == "open"
                )
            )
            or 0
        )

        contributors_count = (
            await self.session.scalar(
                select(func.count(func.distinct(Commit.author_email))).where(
                    Commit.repository_id.in_(repo_ids)
                )
            )
            or 0
        )

        return {
            "total_commits": commits_count,
            "pull_requests": prs_count,
            "open_issues": open_issues_count,
            "contributors": contributors_count,
        }

    async def get_recent_activity(self, repo_ids: list[UUID], limit: int = 20) -> list[dict]:
        if not repo_ids:
            return []

        # Commits
        commits_result = await self.session.execute(
            select(Commit)
            .options(joinedload(Commit.repository))
            .where(Commit.repository_id.in_(repo_ids))
            .order_by(Commit.commit_date.desc())
            .limit(limit)
        )
        commits = commits_result.scalars().all()

        # PRs
        prs_result = await self.session.execute(
            select(PullRequest)
            .options(joinedload(PullRequest.repository))
            .where(PullRequest.repository_id.in_(repo_ids))
            .order_by(PullRequest.created_at_meta.desc())
            .limit(limit)
        )
        prs = prs_result.scalars().all()

        # Issues
        issues_result = await self.session.execute(
            select(Issue)
            .options(joinedload(Issue.repository))
            .where(Issue.repository_id.in_(repo_ids))
            .order_by(Issue.created_at_meta.desc())
            .limit(limit)
        )
        issues = issues_result.scalars().all()

        activity = []
        for c in commits:
            activity.append(
                {
                    "id": str(c.id),
                    "type": "commit",
                    "title": c.message.split("\n")[0] if c.message else "Commit",
                    "author": c.author_name,
                    "timestamp": c.commit_date.isoformat(),
                    "repository": f"{c.repository.owner}/{c.repository.name}",
                }
            )

        for p in prs:
            activity.append(
                {
                    "id": str(p.id),
                    "type": "pull_request",
                    "title": f"#{p.number} {p.title}",
                    "author": p.author,
                    "timestamp": p.created_at_meta.isoformat(),
                    "repository": f"{p.repository.owner}/{p.repository.name}",
                }
            )

        for i in issues:
            activity.append(
                {
                    "id": str(i.id),
                    "type": "issue",
                    "title": f"#{i.number} {i.title}",
                    "author": i.author,
                    "timestamp": i.created_at_meta.isoformat(),
                    "repository": f"{i.repository.owner}/{i.repository.name}",
                }
            )

        # Sort by timestamp desc
        activity.sort(key=lambda x: x["timestamp"], reverse=True)
        return activity[:limit]
