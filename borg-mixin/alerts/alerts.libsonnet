{
  prometheusAlerts+:: {
    groups+: [
      {
        name: 'borg',
        rules: [
          {
            alert: 'BorgMissingBackup',
            expr: 'time() - sum by (repo, instance) (borg_last_backup_timestamp{%(borgSelector)s}) > %(backupThreshold)s' % $._config,
            labels: {
              severity: 'warning',
            },
            annotations: {
              summary: 'Borg missing backup.',
              description: 'The instance {{ $labels.instance }} has not created a backup of the repo {{ $labels.repo }} in the last {{ $value }} seconds.',
            },
            'for': '1m',
          },
        ],
      },
    ],
  },
}
