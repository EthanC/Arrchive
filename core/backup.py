from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Self

from loguru import logger


class Source(str, Enum):
    """An Enum containing members representing backup sources."""

    Bazarr = "Bazarr"
    Prowlarr = "Prowlarr"
    Radarr = "Radarr"
    Sonarr = "Sonarr"

    def __str__(self: Self) -> str:
        """Return the value of the provided Enum member."""

        return self.value

    def color(self: Self) -> str:
        """Return the brand hexidecimal color code for the provided backup source."""

        match self:
            case Source.Bazarr:
                return "BE4BDB"
            case Source.Prowlarr:
                return "E66001"
            case Source.Radarr:
                return "FFC12F"
            case Source.Sonarr:
                return "00CCFF"
            case _:
                logger.warning(f"Failed to find color for source {self}")

                return

    def icon(self: Self) -> str:
        """Return the brand icon URL for the provided backup source."""

        match self:
            case Source.Bazarr:
                return "https://raw.githubusercontent.com/morpheus65535/bazarr/refs/heads/master/frontend/public/images/logo128.png"
            case Source.Prowlarr:
                return "https://raw.githubusercontent.com/Prowlarr/Prowlarr/refs/heads/develop/Logo/1024.png"
            case Source.Radarr:
                return "https://raw.githubusercontent.com/Radarr/Radarr/refs/heads/develop/Logo/1024.png"
            case Source.Sonarr:
                return "https://raw.githubusercontent.com/Sonarr/Sonarr/refs/heads/v5-develop/Logo/1024.png"
            case _:
                logger.warning(f"Failed to find icon for source {self}")

                return


class Action(str, Enum):
    """An Enum containing members representing backup actions."""

    Uploaded = "Uploaded"
    Deleted = "Deleted"

    def __str__(self: Self) -> str:
        """Return the value of the provided Enum member."""

        return self.value


class Backup:
    """A class containing properties for a Backup object."""

    def __init__(
        self: Self,
        source: Source,
        source_version: str,
        timestamp: datetime,
        file_name: str,
        local_path: Path | None = None,
        drive_url: str | None = None,
        drive_id: str | None = None,
    ) -> None:
        """Initialize a Backup object."""

        self.source: Source = source
        self.source_version: str = source_version
        self.timestamp: datetime = timestamp
        self.timestamp_formatted: str = timestamp.strftime("%A, %B %#d, %Y %I:%M %p")
        self.file_name: str = file_name
        self.local_path: Path | None = local_path
        self.drive_url: str | None = drive_url
        self.drive_id: str | None = drive_id

    def __repr__(self: Self) -> str:
        """Return a string representation of the provided Backup object."""

        return (
            f"Backup(, "
            + f"source={self.source!r}, "
            + f"source_version={self.source_version!r}, "
            + f"timestamp={self.timestamp!r}, "
            + f"timestamp_formatted={self.timestamp_formatted!r}, "
            + f"file_name={self.file_name!r}, "
            + f"local_path={self.local_path!r}, "
            + f"drive_url={self.drive_url!r}, "
            + f"drive_id={self.drive_id!r}"
            + ")"
        )

    @classmethod
    def create(
        cls: type[Self],
        source: Source,
        file_name: str,
        local_path: Path | None = None,
        drive_url: str | None = None,
        drive_id: str | None = None,
    ) -> Self | None:
        """Create and return a new Backup object with the provided arguments."""

        backup: Self | None = None

        if not file_name.endswith(".zip"):
            logger.warning(f"File {file_name} is not a valid {source} backup")

            return

        try:
            file_name_pieces: list[str] = file_name.split("_", 3)

            timestamp: datetime = datetime.strptime(
                file_name_pieces[3].rsplit(".", 1)[0], "%Y.%m.%d_%H.%M.%S"
            )
            source_version: str = file_name_pieces[2]

            backup = cls(
                source,
                source_version,
                timestamp,
                file_name,
                local_path,
                drive_url,
                drive_id,
            )
        except Exception as e:
            logger.opt(exception=e).error(
                f"Failed to create {source} backup object from file {file_name}"
            )

            return

        logger.trace(f"{backup=}")

        return backup


def backup_term(number: int) -> str:
    """Return the proper term for the provided value."""

    if number == 1:
        return "backup"

    return "backups"


def sort_backups(backups: list[Backup]) -> list[Backup]:
    """Return a list of backup objects sorted from newest to oldest."""

    return sorted(backups, key=lambda backup: backup.timestamp, reverse=True)
