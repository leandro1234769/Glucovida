import json
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
from typing import Literal

from app.schemas.auth import ConsentVersions


Environment = Literal["development", "test", "production"]


class LegalDocumentsUnavailable(ValueError):
    """The configured documents cannot be used in this environment."""


@dataclass(frozen=True)
class LegalDocument:
    kind: str
    version: str
    status: str
    sha256: str
    approved_at: str | None = None
    approval_reference: str | None = None


def current_legal_documents(
    versions: ConsentVersions, environment: Environment
) -> tuple[LegalDocument, ...]:
    directory = files("app.legal").joinpath("documents")
    manifest = [
        LegalDocument(**record)
        for record in json.loads(directory.joinpath("manifest.json").read_text(encoding="utf-8"))
    ]
    status = {"development": "draft", "test": "test", "production": "approved"}[environment]
    selected = []
    for kind, version in (
        ("terms", versions.terms_version),
        ("privacy", versions.privacy_version),
        ("health_data", versions.health_data_version),
    ):
        matches = [entry for entry in manifest if entry.kind == kind and entry.version == version]
        if len(matches) != 1:
            raise LegalDocumentsUnavailable(f"Unknown or duplicate legal document: {kind} {version}")
        document = matches[0]
        if document.status != status or (
            status == "approved" and not (document.approved_at and document.approval_reference)
        ):
            raise LegalDocumentsUnavailable(f"Document {version} is not valid for {environment}")
        body = directory.joinpath(f"{version}.md").read_text(encoding="utf-8")
        digest = sha256(body.encode("utf-8")).hexdigest()
        if digest != document.sha256:
            raise LegalDocumentsUnavailable(f"Document checksum mismatch: {version}")
        selected.append(document)
    return tuple(selected)
