# borg-exporter [![Build Status](https://ci.depode.com/api/badges/danihodovic/borg-exporter/status.svg)](https://ci.depode.com/danihodovic/borg-exporter)

A Prometheus exporter for [Borg](https://github.com/borgbackup/borg) backups.

It provides the following metrics:

Name     | Description | Type
---------|-------------|----
borg_backups_total | Total number of Borg backups | Gauge
borg_last_backup_timestamp | Timestamp of the last backup | Gauge
