# Getan to zeiterfassung

Queries entries from [getan](https://heptapod.host/intevation/getan/)'s database and compares them with the zeiterfassung.txt files.
The files are located automatically.

Only works with one-line entries in zeiterfassung.txt (default behaviour).

In automatic mode, the user gets an editor with the proposed changes for review.
If the destination directory is a hg Repository, the commit is also to be reviewed by the user.
