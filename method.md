1. borgmatic info --json
2. borgmatic list --json

Expose gauge


    "repository": {
      "id": "ce53a0e8b59c14b9a0dc156ab574d721010f76e4f90f37e8c8456adb2bd9d1b1",
      "last_modified": "2021-05-10T22:00:51.000000",
      "location": "ssh://root@172.16.140.5/opt/borg_backups/owa"
    }

    [
      {
        "archives": [
          {
            "archive": "webtelowa-bin-190930-2021-05-03T22:00:04",
            "barchive": "webtelowa-bin-190930-2021-05-03T22:00:04",
            "id": "58af4eeac65b3a03705b636211434d657016a1993dd4ea3bf23f8d5ac653e515",
            "name": "webtelowa-bin-190930-2021-05-03T22:00:04",
            "start": "2021-05-03T22:00:05.000000",
            "time": "2021-05-03T22:00:05.000000"
          },
          {
            "archive": "webtelowa-bin-190930-2021-05-04T22:00:04",
            "barchive": "webtelowa-bin-190930-2021-05-04T22:00:04",
            "id": "05357bd9b32e0f3d1cce7e683f57d1f7a7b52f7904895c009387bc5b56ad6ecf",
            "name": "webtelowa-bin-190930-2021-05-04T22:00:04",
            "start": "2021-05-04T22:00:05.000000",
            "time": "2021-05-04T22:00:05.000000"
          },



One exporter, multiple backups?

Webtel:

OWA
Staging
Prod


Depode:
CI
Prod


Labels:
- repo
- location

"location": "ssh://root@172.16.140.5/opt/borg_backups/owa"

Metrics:
borg_backups_total{repo}
borg_last_backup_timestamp{repo} = timestamp   --- if this is too long ago, alert
# borg_next_scheduled_backup{repo} = timestamo   ---
time() -kube_cronjob_next_schedule_time > 3600

