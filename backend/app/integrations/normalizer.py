from datetime import UTC, datetime
from uuid import UUID

from app.models.integration import Commit, DriveFile, Issue, NotionPage, PullRequest


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


class NotionNormalizer:
    def _parse_date(self, date_str: str | None) -> datetime:
        if not date_str:
            return datetime.now(UTC)
        try:
            normalized_str = date_str.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized_str)
        except Exception:
            return datetime.now(UTC)

    def normalize_page(self, integration_id: UUID, raw_data: dict) -> NotionPage:
        title = "Untitled Page"
        obj_type = raw_data.get("object", "page")

        if obj_type == "database":
            title_list = raw_data.get("title", [])
            if title_list:
                title = "".join(t.get("plain_text", "") for t in title_list)
        else:
            properties = raw_data.get("properties", {})
            for prop in properties.values():
                if prop.get("type") == "title":
                    title_list = prop.get("title", [])
                    if title_list:
                        title = "".join(t.get("plain_text", "") for t in title_list)
                    break

        parent = raw_data.get("parent", {})
        parent_id = None
        if parent.get("type") == "page_id":
            parent_id = parent.get("page_id")
        elif parent.get("type") == "database_id":
            parent_id = parent.get("database_id")

        last_edited_by = raw_data.get("last_edited_by", {})
        author = last_edited_by.get("id", "unknown")
        if last_edited_by.get("object") == "user" and last_edited_by.get("name"):
            author = last_edited_by.get("name")

        return NotionPage(
            integration_id=integration_id,
            notion_page_id=raw_data.get("id", ""),
            parent_id=parent_id,
            title=title or "Untitled Page",
            url=raw_data.get("url"),
            last_edited=self._parse_date(raw_data.get("last_edited_time")),
            created_time=self._parse_date(raw_data.get("created_time")),
            author=author,
            archived=raw_data.get("archived", False),
        )


class GoogleDriveNormalizer:
    def _parse_date(self, date_str: str | None) -> datetime:
        if not date_str:
            return datetime.now(UTC)
        try:
            normalized_str = date_str.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized_str)
        except Exception:
            return datetime.now(UTC)

    def normalize_file(
        self, integration_id: UUID, raw_data: dict, content: str | None = None
    ) -> DriveFile:
        parents = raw_data.get("parents", [])
        parent_folder = parents[0] if parents else None

        size_raw = raw_data.get("size")
        file_size = int(size_raw) if size_raw is not None else None

        owners = raw_data.get("owners", [])
        owner = None
        if owners:
            owner = owners[0].get("displayName") or owners[0].get("emailAddress")

        return DriveFile(
            integration_id=integration_id,
            google_file_id=raw_data.get("id", ""),
            name=raw_data.get("name", "Untitled File"),
            mime_type=raw_data.get("mimeType", "application/octet-stream"),
            parent_folder=parent_folder,
            file_size=file_size,
            owner=owner,
            url=raw_data.get("webViewLink"),
            created_time=self._parse_date(raw_data.get("createdTime")),
            modified_time=self._parse_date(raw_data.get("modifiedTime")),
            archived=raw_data.get("trashed", False),
            content=content,
        )
