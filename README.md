# Scripts

- getan:
  - Update zeiterfassung.txt from getan
- logbuch tools
  - bash completions

## Getan

### Getan to zeiterfassung

Queries entries from [getan](https://heptapod.host/intevation/getan/)'s database and compares them with the zeiterfassung.txt files.
The files are located automatically.

Only works with one-line entries in zeiterfassung.txt (default behaviour).

In automatic mode, the user gets an editor with the proposed changes for review.

If the project directory is an hg repository, the script makes a clone (if it exists pulls and updates it).
Local clones are located in `~/.getan/hg-repos/<projectid>/`.
The script inserts the new entries, the user reviews the change and enters the commit message.
Then the change is pushed to the upstream repository.
If the clone ends up with more than one head, a warning is shown.

### Configuration

The script reads optional configuration from `~/.getan/config.ini`.
The file is ignored if it does not exist.

```ini
# ~/.getan/config.ini

[zz-update]
# Comma-separated project keys to ignore
# ignored_keys = A,w,o,Q,B,ü,M,u,k

# Comma-separated project keys that cannot be auto-resolved
# impossible_keys = q

# Initials to use in zeiterfassung.txt entries.
# initials = abc

[zz-update:manual-mappings]
# Manually map a project ID to its project root directory when auto-detection fails.
# 1234 = /home/clients/company/1234-project
# example = /home/activities/pflege-example
```

## Docker

### docker-prune

Removes unused Docker objects (containers, networks, images) older than 30 days.
Images not in use are always removed after 7 days.

Suitable for use with `chronic -e` in cron for exit-code alerting without mail on normal output.
Output is written to the systemd journal (`journalctl -t docker-prune`).

### Exceptions

`docker-prune.sh` accepts an optional shell file as its first argument where exceptions can be defined.
All exception filters are combined (logical AND) together. Available options with examples:

```sh
PRUNE_EXCEPTION_IMAGE=sha256:5af1ab82af1afdd3ff64df7dabf984f32684aa5c65517fcff59d123a4af45603
PRUNE_EXCEPTION_PROJECT_WORKING_DIR=/home/USERNAME/netbox-ot-assetdatabase_dev
PRUNE_EXCEPTION_PROJECT=netbox-ot-assetdatabase_dev
PRUNE_EXCEPTION_MAINTAINER=first.last@intevation.de
```

Filters apply to containers only, not images.
Images are always removed after 7 days if unused.

## Logbuch

### Bash completions

Place `logbuch/bash_completion` in `/etc/bash_completion.d/logbuch` to enable completions for logbuch tools.

It completes these commands:
- `apt-install`
- `apt-remove`
- `apt-autoremove`
- `apt-build-dep`
- `apt-upgrade`
- `apt-dist-upgrade`

logbuch tools: https://hg.intevation.de/adminton/
