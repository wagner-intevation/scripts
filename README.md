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
If the destination directory is a hg Repository, the commit is also to be reviewed by the user.

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
