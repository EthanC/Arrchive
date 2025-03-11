# Arrchive

![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/EthanC/Arrchive/ci.yaml?branch=main) ![Docker Pulls](https://img.shields.io/docker/pulls/ethanchrisp/Arrchive?label=Docker%20Pulls) ![Docker Image Size (tag)](https://img.shields.io/docker/image-size/ethanchrisp/arrchive/latest?label=Docker%20Image%20Size)

Arrchive mirrors [Radarr](https://github.com/Radarr/Radarr), [Sonarr](https://github.com/Sonarr/Sonarr), [Prowlarr](https://github.com/Prowlarr/Prowlarr), and [Bazarr](https://github.com/morpheus65535/bazarr) database backups to Google Drive.

<p align="center">
    <img src="https://i.imgur.com/jmLZ8gY.png" draggable="false">
</p>

## Setup

Although not required, a [Discord Webhook](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) is recommended for notifications.

Arrchive is intended to be run at an interval using a task scheduler, such as [cron](https://crontab.guru/).

**Environment Variables:**

-   `LOG_LEVEL`: [Loguru](https://loguru.readthedocs.io/en/stable/api/logger.html) severity level to write to the console.
-   `LOG_DISCORD_WEBHOOK_URL`: [Discord Webhook](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) URL to receive log events.
-   `LOG_DISCORD_WEBHOOK_LEVEL`: Minimum [Loguru](https://loguru.readthedocs.io/en/stable/api/logger.html) severity level to forward to Discord.
-   `DISCORD_WEBHOOK_URL`: [Discord Webhook](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) URL to receive backup action notifications.
-   `BAZARR_BACKUP_PATH`: Path to a directory containing database backup `.zip` files for [Bazarr](https://github.com/morpheus65535/bazarr).
-   `PROWLARR_BACKUP_PATH`: Path to a directory containing database backup `.zip` files for [Prowlarr](https://github.com/Prowlarr/Prowlarr).
-   `RADARR_BACKUP_PATH`: Path to a directory containing database backup `.zip` files for [Radarr](https://github.com/Radarr/Radarr).
-   `SONARR_BACKUP_PATH`: Path to a directory containing database backup `.zip` files for [Sonarr](https://github.com/Sonarr/Sonarr).
-   `GOOGLE_SERVICE_EMAIL`: Email Address for a [Google Service Account](https://console.cloud.google.com/projectselector/iam-admin/serviceaccounts).
-   `GOOGLE_SERVICE_CLIENT_ID`: Client ID for a [Google Service Account](https://console.cloud.google.com/projectselector/iam-admin/serviceaccounts).
-   `GOOGLE_SERVICE_PRIVATE_KEY_ID`: Private Key ID for a [Google Service Account](https://console.cloud.google.com/projectselector/iam-admin/serviceaccounts).
-   `GOOGLE_SERVICE_PRIVATE_KEY`: Private Key for a [Google Service Account](https://console.cloud.google.com/projectselector/iam-admin/serviceaccounts).
-   `GOOGLE_DRIVE_FOLDER_ID`: Identifier for a Google Drive folder derrived from its URL.
-   `BACKUP_RETAIN_LIMIT`: Number of backup files to retain on a per-application basis.

### Google Drive (Required)

1. Create a new Project in the [Google Cloud console](https://console.developers.google.com/iam-admin/projects).
    - (Recommended) Project Name: `Arrchive`
    - After creation, select the Project.
2. Enable the [Google Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com) for the Arrchive project.
3. Create a new [Service Account](https://console.cloud.google.com/projectselector/iam-admin/serviceaccounts/create?walkthrough_id=iam--create-service-account#step_index=1) for the Arrchive project.
    - (Recommended) Servive Account Name: `Arrchive`
    - (Recommended) Service Account Description: `https://github.com/EthanC/Arrchive`
    - _Create and Continue_
4. Grant the Arrchive Service Account access to the Arrchive project.
    - (Recommended) Service Account Role: `Owner`
    - _Continue_ -> _Done_
5. Obtain a Private Key for the [Service Account](https://console.cloud.google.com/projectselector/iam-admin/serviceaccounts).
    - _Actions_ -> _Manage Keys_ -> _Add Key_ -> _Create a new Key_ -> _JSON_ -> _Private Key saved to your Computer_
6. Set the corresponding environment variables using the values in the JSON file.
7. Open [Google Drive](https://drive.google.com/) and create a folder for \*Arr application backups to be stored.
    - (Recommended) Folder Name: `Arrchive`
8. Share the backup folder to the Service Account email address with Editor permissions.
9. Open the Arrchive folder and copy its ID from the page URL.
    - Example: `https://drive.google.com/drive/folders/ARRCHIVE_FOLDER_ID`
    - Set the `GOOGLE_DRIVE_FOLDER_ID` environment variable to this value.

### Docker (Recommended)

Modify the following `compose.yaml` example file, then run `docker compose up`.

```yaml
services:
  arrchive:
    container_name: arrchive
    image: ethanchrisp/arrchive:latest
    environment:
      LOG_LEVEL: INFO
      LOG_DISCORD_WEBHOOK_URL: https://discord.com/api/webhooks/YYYYYYYY/YYYYYYYY
      LOG_DISCORD_WEBHOOK_LEVEL: WARNING
      DISCORD_WEBHOOK_URL: https://discord.com/api/webhooks/XXXXXXXX/XXXXXXXX
      BAZARR_BACKUP_PATH: /path/to/bazarr/backups
      PROWLARR_BACKUP_PATH: /path/to/prowlarr/backups
      RADARR_BACKUP_PATH: /path/to/radarr/backups
      SONARR_BACKUP_PATH: /path/to/sonarr/backups
      GOOGLE_SERVICE_EMAIL: email@gserviceaccount.com
      GOOGLE_SERVICE_CLIENT_ID: 000000000000000000000
      GOOGLE_SERVICE_PRIVATE_KEY_ID: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
      GOOGLE_SERVICE_PRIVATE_KEY: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
      GOOGLE_DRIVE_FOLDER_ID: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
      BACKUP_RETAIN_LIMIT: 3
```

### Standalone

Arrchive is built for [Python 3.13](https://www.python.org/) or greater, compatability with prior versions is not guaranteed.

1. Install required dependencies using [uv](https://github.com/astral-sh/uv): `uv sync`
2. Rename `.env.example` to `.env`, then provide the environment variables.
3. Start Arrchive: `uv run arrchive.py`

## Thanks

-   Arrchive uses a [Pirate icon](https://thenounproject.com/icon/pirate-3201839/) created by [Adrien Coquet](https://thenounproject.com/creator/coquet_adrien/) via [Noun Project](https://thenounproject.com/).
