import logging
from datetime import datetime
from os import environ
from pathlib import Path
from sys import stdout
from urllib.parse import ParseResult

from discord_webhook import (  # pyright: ignore [reportMissingTypeStubs]
    DiscordEmbed,
    DiscordWebhook,
)
from environs import env
from loguru import logger
from loguru_discord import DiscordSink
from pydrive2.auth import GoogleAuth  # pyright: ignore [reportMissingTypeStubs]
from pydrive2.drive import (  # pyright: ignore [reportMissingTypeStubs]
    GoogleDrive,
    GoogleDriveFile,
)

from core.backup import Action, Backup, Source, backup_term, sort_backups
from core.intercept import Intercept


def start() -> None:
    """Initialize Arrchive and begin primary functionality."""

    logger.success("Arrchive")
    logger.success("https://github.com/EthanC/Arrchive")

    # Reroute standard logging to Loguru
    logging.basicConfig(handlers=[Intercept()], level=0, force=True)

    if env.read_env(recurse=False):
        logger.info("Loaded environment variables")

    if level := env.str("LOG_LEVEL"):
        logger.remove()
        logger.add(stdout, level=level)

        logger.info(f"Set console logging level to {level}")

    if environ.get("LOG_DISCORD_WEBHOOK_URL"):
        url: ParseResult = env.url("LOG_DISCORD_WEBHOOK_URL")

        logger.add(
            DiscordSink(url.geturl()),
            level=env.str("LOG_DISCORD_WEBHOOK_LEVEL"),
            backtrace=False,
        )

        logger.info("Enabled logging to Discord webhook")
        logger.trace(f"{url=}")

    drive: GoogleDrive | None = drive_authenticate()

    if not drive:
        logger.debug("Exiting due to lack of Google Drive authentication")

        return

    drive_backups: dict[str, list[Backup]] = drive_collect(drive)
    local_backups: dict[str, list[Backup]] = {}

    if environ.get(f"{Source.Bazarr.upper()}_BACKUP_PATH"):
        local_backups[Source.Bazarr] = local_collect(
            Source.Bazarr,
            env.path(f"{Source.Bazarr.upper()}_BACKUP_PATH"),
            drive_backups,
        )

    if environ.get(f"{Source.Prowlarr.upper()}_BACKUP_PATH"):
        local_backups[Source.Prowlarr] = local_collect(
            Source.Prowlarr,
            env.path(f"{Source.Prowlarr.upper()}_BACKUP_PATH"),
            drive_backups,
        )

    if environ.get(f"{Source.Profilarr.upper()}_BACKUP_PATH"):
        local_backups[Source.Profilarr] = local_collect(
            Source.Profilarr,
            env.path(f"{Source.Profilarr.upper()}_BACKUP_PATH"),
            drive_backups,
        )

    if environ.get(f"{Source.Radarr.upper()}_BACKUP_PATH"):
        local_backups[Source.Radarr] = local_collect(
            Source.Radarr,
            env.path(f"{Source.Radarr.upper()}_BACKUP_PATH"),
            drive_backups,
        )

    if environ.get(f"{Source.Sonarr.upper()}_BACKUP_PATH"):
        local_backups[Source.Sonarr] = local_collect(
            Source.Sonarr,
            env.path(f"{Source.Sonarr.upper()}_BACKUP_PATH"),
            drive_backups,
        )

    drive_uploaded: int = 0
    drive_deleted: int = 0

    if environ.get("GOOGLE_DRIVE_FOLDER_ID"):
        drive_uploaded = drive_upload(drive, local_backups, drive_backups)

    if environ.get("BACKUP_RETAIN_LIMIT"):
        # Update the list of Google Drive backups
        drive_backups = drive_collect(drive)

        drive_deleted = drive_delete(drive, drive_backups)

    drive_total: int = drive_uploaded + drive_deleted

    logger.success(
        f"Processed {drive_total:,} {backup_term(drive_total)} ({drive_uploaded:,} uploaded / {drive_deleted:,} deleted)"
    )


def local_collect(
    source: Source, local_path: Path, drive_backups: dict[str, list[Backup]]
) -> list[Backup]:
    """Return local backups for the provided backup source."""

    local_backups: list[Backup] = []

    if local_path.is_dir() and local_path.exists():
        for local_file in local_path.glob("**/*.zip"):
            logger.trace(f"{local_file=}")

            drive_backup_exists: bool = False

            if local_file.is_dir():
                logger.debug(f"Skipped {local_file.name} for {source}, is a directory")

                continue

            local_backup: Backup | None = Backup.create(
                source, local_file.name, local_file.resolve()
            )

            if not local_backup:
                logger.debug(f"Skipping {local_file}, backup object is null")

                continue

            for drive_backup in drive_backups[source]:
                if local_backup.file_name == drive_backup.file_name:
                    drive_backup_exists = True

            if drive_backup_exists:
                logger.debug(
                    f"Skipping {local_backup.file_name}, backup already exists in Google Drive"
                )

                continue

            local_backups.append(local_backup)
    else:
        logger.error(f"{local_path} is not a valid local {source} backup path")

    if environ.get("BACKUP_RETAIN_LIMIT"):
        count_current = len(local_backups)
        retain_limit: int = env.int("BACKUP_RETAIN_LIMIT")
        if count_current > retain_limit:
            local_backups = local_backups[retain_limit:]

            logger.debug(
                f"Discarded {(count_current - retain_limit):,} {source} backups due to retention limit"
            )

    logger.info(
        f"Collected {len(local_backups):,} local {source} {backup_term(len(local_backups))}"
    )
    logger.trace(f"{local_backups=}")

    return local_backups


def drive_authenticate() -> GoogleDrive | None:
    """
    Authenticate with Google Drive using a Service Account with the
    configured credentials.
    """

    auth: GoogleAuth | None = None
    drive: GoogleDrive | None = None

    try:
        auth = GoogleAuth(
            settings={
                "client_config_backend": "service",
                "service_config": {
                    "client_json_dict": {
                        "type": "service_account",
                        "private_key_id": env.str("GOOGLE_SERVICE_PRIVATE_KEY_ID"),
                        "private_key": env.str("GOOGLE_SERVICE_PRIVATE_KEY").replace(
                            "\\n", "\n"
                        ),
                        "client_email": env.str("GOOGLE_SERVICE_EMAIL"),
                        "client_id": env.str("GOOGLE_SERVICE_CLIENT_ID"),
                    },
                    "oauth_scope": [
                        "https://www.googleapis.com/auth/drive",
                        "https://www.googleapis.com/auth/drive.metadata",
                    ],
                },
            }
        )

        auth.ServiceAuth()

        drive = GoogleDrive(auth)
    except Exception as e:
        logger.opt(exception=e).critical(f"Failed to authenticate with Google Drive")
        logger.debug(f"{auth=}")
        logger.debug(f"{drive=}")

    if auth and drive:
        logger.info("Authenticated with Google Drive")
        logger.trace(f"{auth=}")
        logger.trace(f"{drive=}")

    return drive


def drive_collect(drive: GoogleDrive) -> dict[str, list[Backup]]:
    """Return Google Drive backups for all backup sources."""

    folder_id: str = env.str("GOOGLE_DRIVE_FOLDER_ID")

    raw: list[GoogleDriveFile] = []
    drive_backups: dict[str, list[Backup]] = {}

    for source in Source:
        drive_backups[source] = []

    try:
        raw = drive.ListFile(  # pyright: ignore [reportUnknownMemberType, reportUnknownVariableType]
            {"q": f"'{folder_id}' in parents and trashed=false"}
        ).GetList()
    except Exception as e:
        logger.opt(exception=e).error(
            f"Failed to collect backups from Google Drive folder {folder_id}"
        )

    logger.trace(f"{raw=}")

    for entry in raw:  # pyright: ignore [reportUnknownVariableType]
        logger.trace(f"{entry=}")

        file_name: str = str(entry["title"])  # pyright: ignore [reportUnknownArgumentType]

        for source in Source:
            if file_name.startswith(f"{source.lower()}_backup_"):
                drive_backup: Backup | None = Backup.create(
                    source,
                    file_name,
                    None,
                    str(entry["alternateLink"]),  # pyright: ignore [reportUnknownArgumentType]
                    str(entry["id"]),  # pyright: ignore [reportUnknownArgumentType]
                )

                if not drive_backup:
                    logger.debug(f"Skipping {entry}, backup object is null")

                    continue

                drive_backups[source].append(drive_backup)

    logger.info(
        f"Collected {len(drive_backups):,} Google Drive {backup_term(len(drive_backups))}"
    )

    return drive_backups


def drive_upload(
    drive: GoogleDrive,
    local_backups: dict[str, list[Backup]],
    drive_backups: dict[str, list[Backup]],
) -> int:
    """
    Iterate the collected local backup files and upload each to Google Drive
    if it does not already exist in the configured folder.
    """

    upload_count_total: int = 0
    retain_limit: int | None = None

    if environ.get("BACKUP_RETAIN_LIMIT"):
        retain_limit = env.int("BACKUP_RETAIN_LIMIT")

    for source in local_backups:
        upload_count_source: int = 0

        local_backups[source] = sort_backups(local_backups[source])
        drive_backups[source] = sort_backups(drive_backups[source])

        drive_backup_newer: bool = False

        for local_backup in local_backups[source]:
            if retain_limit:
                if upload_count_source >= retain_limit:
                    logger.debug(
                        f"Skipped {local_backup.source} backup {local_backup.timestamp_formatted}, retention limit reached"
                    )

                    continue

            if not local_backup.local_path:
                logger.debug(
                    f"Skipped {local_backup.source} backup {local_backup.timestamp_formatted}, does not exist locally"
                )

                continue
            elif local_backup.drive_url:
                logger.debug(
                    f"Skipped {local_backup.source} backup {local_backup.timestamp_formatted}, already exists in Google Drive"
                )

                continue

            if environ.get("BACKUP_RETAIN_LIMIT"):
                for drive_backup in drive_backups[source]:
                    if local_backup.timestamp <= drive_backup.timestamp:
                        drive_backup_newer = True

            if drive_backup_newer:
                logger.debug(
                    f"Skipped {local_backup.source} backup {local_backup.timestamp_formatted}, retention limit reached and a newer backup exists in Google Drive"
                )

                continue

            try:
                file: GoogleDriveFile = drive.CreateFile(  # pyright: ignore [reportUnknownMemberType]
                    {
                        "title": local_backup.file_name,
                        "parents": [{"id": env.str("GOOGLE_DRIVE_FOLDER_ID")}],
                    }
                )

                file.SetContentFile(local_backup.local_path.resolve())  # pyright: ignore [reportUnknownMemberType]
                file.Upload()  # pyright: ignore [reportUnknownMemberType]

                local_backup.drive_url = (
                    str(file["alternateLink"]) if file["alternateLink"] else None  # pyright: ignore [reportUnknownArgumentType]
                )

                upload_count_total += 1
                upload_count_source += 1
            except Exception as e:
                logger.opt(exception=e).error(
                    f"Failed to upload {local_backup.source} backup {local_backup.timestamp_formatted} to Google Drive"
                )

                continue

            logger.trace(f"{file=}")
            logger.info(
                f"Uploaded {local_backup.source} backup {local_backup.timestamp_formatted} to Google Drive"
            )
            logger.debug(f"{local_backup.drive_url=}")

            if environ.get("DISCORD_WEBHOOK_URL"):
                notify(local_backup, Action.Uploaded)

    return upload_count_total


def drive_delete(drive: GoogleDrive, drive_backups: dict[str, list[Backup]]) -> int:
    """
    Delete any Google Drive backups that are greater than the configured
    retention limit on a per-source basis.
    """

    deleted: int = 0
    retain_limit: int = env.int("BACKUP_RETAIN_LIMIT")

    for source in drive_backups:
        if len(drive_backups[source]) > retain_limit:
            drive_backups[source] = sort_backups(drive_backups[source])

            # Don't delete the newest [retain_limit] backups
            for drive_backup in drive_backups[source][retain_limit:]:
                if not drive_backup.drive_id:
                    logger.warning(
                        f"Attempted to delete Google Drive {drive_backup.source} backup {drive_backup.timestamp_formatted}, but it has no drive_id"
                    )
                    logger.debug(f"{drive_backup=}")

                    continue

                raw: GoogleDriveFile = drive.CreateFile({"id": drive_backup.drive_id})  # pyright: ignore [reportUnknownMemberType]

                try:
                    raw.Delete()  # pyright: ignore [reportUnknownMemberType]
                except Exception as e:
                    logger.opt(exception=e).error(
                        f"Failed to delete {drive_backup.source} backup {drive_backup.timestamp_formatted} from Google Drive"
                    )

                    continue

                logger.info(
                    f"Deleted Google Drive {drive_backup.source} backup {drive_backup.timestamp_formatted} "
                )
                logger.debug(f"{drive_backup.drive_url=}")
                logger.trace(f"{raw=}")

                if environ.get("DISCORD_WEBHOOK_URL"):
                    notify(drive_backup, Action.Deleted)

    return deleted


def notify(backup: Backup, action: Action) -> None:
    """Report backup actions to the configured Discord webhook."""

    if not backup.drive_url:
        logger.warning(
            f"Attempted to send notification without drive_url for {backup.source} backup {backup.timestamp_formatted}"
        )
        logger.debug(f"{backup=}")

        return

    embed: DiscordEmbed = DiscordEmbed()

    embed.set_color(backup.source.color())
    embed.set_author(backup.source, icon_url=backup.source.icon())
    embed.set_title(f"Backup {action}")
    embed.set_thumbnail("https://i.imgur.com/bOn2yC4.png")
    embed.add_embed_field("Timestamp", f"<t:{int(backup.timestamp.timestamp())}:F>")
    embed.set_footer("Arrchive", icon_url="https://i.imgur.com/pynYfuR.png")  # pyright: ignore [reportUnknownMemberType]
    embed.set_timestamp(datetime.now().timestamp())

    if backup.source_version:
        embed.add_embed_field("Version", backup.source_version)

    if action == Action.Uploaded:
        embed.set_url(backup.drive_url)

    logger.trace(f"{embed=}")

    try:
        DiscordWebhook(
            env.url("DISCORD_WEBHOOK_URL").geturl(),
            embeds=[embed],
            rate_limit_retry=True,
        ).execute()
    except Exception as e:
        logger.opt(exception=e).error(
            f"Failed to send notification for {backup.source} backup {backup.timestamp_formatted}"
        )


if __name__ == "__main__":
    try:
        start()
    except KeyboardInterrupt:
        pass
