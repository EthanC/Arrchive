# Arrchive

![Python](https://img.shields.io/badge/Python-3-blue?logo=python&logoColor=white)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/ethanc/arrchive/ci.yaml)
![Docker Pulls](https://img.shields.io/docker/pulls/ethanchrisp/arrchive)
![Docker Image Size (tag)](https://img.shields.io/docker/image-size/ethanchrisp/arrchive)

Arrchive uploads mirrors of your \*Arr app database backups to [Google Drive](https://drive.google.com/).

It's lightweight, runs in Docker, features a configurable retention limit, and optionally sends notifications via Discord.

**Supported \*Arr Apps:**

-   [Radarr](https://github.com/Radarr/Radarr)
-   [Sonarr](https://github.com/Sonarr/Sonarr)
-   [Prowlarr](https://github.com/Prowlarr/Prowlarr)
-   [Bazarr](https://github.com/morpheus65535/bazarr)
-   [Profilarr](https://github.com/Dictionarry-Hub/Profilarr)

<p align="center">
    <img src="https://i.imgur.com/jmLZ8gY.png" alt="An example of an Arrchive notification in Discord." draggable="false">
</p>

## Features

-   Uploads compressed `.zip` backups from your \*Arr apps to Google Drive.
-   Automatically removes old backup mirrors based on your retention limit.
-   Optional Discord integration for logs and backup notifications.
-   Easy to deploy via Docker or run standalone with Python.

## Getting Started

### Quick Start: Docker Compose

> [!NOTE]
> Arrchive is designed to run on a schedule to periodically mirror backups. `cron` is recommended.

Here's an example `compose.yaml` to get started. Run it with `docker compose up`.

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
      BAZARR_BACKUP_PATH: /container/path/to/bazarr/backups
      PROFILARR_BACKUP_PATH: /container/path/to/profilarr/backups
      PROWLARR_BACKUP_PATH: /container/path/to/prowlarr/backups
      RADARR_BACKUP_PATH: /container/path/to/radarr/backups
      SONARR_BACKUP_PATH: /container/path/to/sonarr/backups
      GOOGLE_SERVICE_EMAIL: email@gserviceaccount.com
      GOOGLE_SERVICE_CLIENT_ID: 000000000000000000000
      GOOGLE_SERVICE_PRIVATE_KEY_ID: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
      GOOGLE_SERVICE_PRIVATE_KEY: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
      GOOGLE_DRIVE_FOLDER_ID: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
      BACKUP_RETAIN_LIMIT: 3
    volumes:
      - /local/path/to/bazarr/backups:/container/path/to/bazarr/backups:ro
      - /local/path/to/profilarr/backups:/container/path/to/profilarr/backups:ro
      - /local/path/to/prowlarr/backups:/container/path/to/prowlarr/backups:ro
      - /local/path/to/radarr/backups:/container/path/to/radarr/backups:ro
      - /local/path/to/sonarr/backups:/container/path/to/sonarr/backups:ro
```

### Standalone: Python

> [!NOTE]
> Python 3.13 or later required.

1. Install dependencies.

    ```bash
    uv sync
    ```

2. Rename `.env.example` to `.env` and configure your environment.

3. Run Arrchive

    ```bash
    uv run arrchive.py
    ```

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

### Environment Variables

| Variable                        | Description                                  | Required? |
| ------------------------------- | -------------------------------------------- | --------- |
| `LOG_LEVEL`                     | Loguru console log level.                    | No        |
| `DISCORD_WEBHOOK_URL`           | Notifications for backup success/failure.    | No        |
| `LOG_DISCORD_WEBHOOK_URL`       | For sending log events to Discord.           | No        |
| `LOG_DISCORD_WEBHOOK_LEVEL`     | Minimum log level for Discord logs.          | No        |
| `BAZARR_BACKUP_PATH`            | Local path to Bazarr backup `.zip` files.    | No        |
| `PROFILARR_BACKUP_PATH`         | Local path to Profilarr backup `.zip` files. | No        |
| `PROWLARR_BACKUP_PATH`          | Local path to Prowlarr backup `.zip` files.  | No        |
| `RADARR_BACKUP_PATH`            | Local path to Radarr backup `.zip` files.    | No        |
| `SONARR_BACKUP_PATH`            | Local path to Sonarr backup `.zip` files.    | No        |
| `GOOGLE_SERVICE_EMAIL`          | Google Service Account Email Address.        | Yes       |
| `GOOGLE_SERVICE_CLIENT_ID`      | Google Service Account Client ID.            | Yes       |
| `GOOGLE_SERVICE_PRIVATE_KEY_ID` | Google Service Account Private Key ID.       | Yes       |
| `GOOGLE_SERVICE_PRIVATE_KEY`    | Google Service Account Private key           | Yes       |
| `GOOGLE_DRIVE_FOLDER_ID`        | Folder ID from Google Drive URL.             | Yes       |
| `BACKUP_RETAIN_LIMIT`           | Maximum number of backups to keep per app.   | No        |

## Thanks

-   [Pirate icon](https://thenounproject.com/icon/pirate-3201839/) courtesy of [Adrien Coquet](https://thenounproject.com/creator/coquet_adrien/) via [Noun Project](https://thenounproject.com/icon/pirate-3201839/).
