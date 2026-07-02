from datetime import UTC, datetime
from uuid import UUID

from app.models.integration import Commit, Issue, PullRequest


class BaseNormalizer:
    def normalize_commit(self, repo_id: UUID, raw_data: dict) -> Commit:
        raise NotImplementedError()

    def normalize_pull_request(self, repo_id: UUID, raw_data: dict) -> PullRequest:
        raise NotImplementedError()

    def normalize_issue(self, repo_id: UUID, raw_data: dict) -> Issue:
        raise NotImplementedError()


class GitHubNormalizer(BaseNormalizer):
    def _parse_date(self, date_str: str | None) -> datetime:
        if not date_str:
            return datetime.now(UTC)
        try:
            # Replace Z with +00:00 for ISO parsing compatibility
            normalized_str = date_str.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized_str)
        except Exception:
            return datetime.now(UTC)

    def normalize_commit(self, repo_id: UUID, raw_data: dict) -> Commit:
        commit_data = raw_data.get("commit", {})
        author_data = commit_data.get("author", {})

        return Commit(
            repository_id=repo_id,
            sha=raw_data.get("sha", ""),
            author_name=author_data.get("name", "Unknown"),
            author_email=author_data.get("email", "unknown@example.com"),
            message=commit_data.get("message", ""),
            commit_date=self._parse_date(author_data.get("date")),
        )

    def normalize_pull_request(self, repo_id: UUID, raw_data: dict) -> PullRequest:
        user_data = raw_data.get("user", {})
        closed_at_str = raw_data.get("closed_at")
        merged_at_str = raw_data.get("merged_at")

        return PullRequest(
            repository_id=repo_id,
            github_pr_id=str(raw_data.get("id", "")),
            number=raw_data.get("number", 0),
            title=raw_data.get("title", "Untitled PR"),
            state=raw_data.get("state", "open"),
            author=user_data.get("login", "unknown"),
            created_at_meta=self._parse_date(raw_data.get("created_at")),
            closed_at=self._parse_date(closed_at_str) if closed_at_str else None,
            merged_at=self._parse_date(merged_at_str) if merged_at_str else None,
        )

    def normalize_issue(self, repo_id: UUID, raw_data: dict) -> Issue:
        user_data = raw_data.get("user", {})
        closed_at_str = raw_data.get("closed_at")

        return Issue(
            repository_id=repo_id,
            github_issue_id=str(raw_data.get("id", "")),
            number=raw_data.get("number", 0),
            title=raw_data.get("title", "Untitled Issue"),
            state=raw_data.get("state", "open"),
            author=user_data.get("login", "unknown"),
            created_at_meta=self._parse_date(raw_data.get("created_at")),
            closed_at=self._parse_date(closed_at_str) if closed_at_str else None,
        )
