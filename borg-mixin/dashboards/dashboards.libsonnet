local grafana = import 'github.com/grafana/grafonnet-lib/grafonnet/grafana.libsonnet';
local dashboard = grafana.dashboard;
local row = grafana.row;
local prometheus = grafana.prometheus;
local template = grafana.template;
local graphPanel = grafana.graphPanel;

{
  grafanaDashboards+:: {

    local prometheusTemplate =
      template.datasource(
        'datasource',
        'prometheus',
        'Prometheus',
        hide='',
      ),

    local borgRow =
      row.new(
        title='Borg'
      ),

    local totalBackups = |||
      sum by (repo, instance) (borg_backups_total{%(borgSelector)s})
    ||| % $._config,

    local lastBackupDate = |||
      sum by (repo, instance) (borg_last_backup_timestamp{%(borgSelector)s}) * 1000
    ||| % $._config,

    local secondsSinceLastBackup = |||
      time() - sum by (repo, instance) (borg_last_backup_timestamp{%(borgSelector)s})
    ||| % $._config,

    'dashboard.json':
      dashboard.new(
        'Borg Backups',
        time_from='now-12h',
      )
      .addPanel(borgRow, gridPos={ h: 1, w: 24, x: 0, y: 0 })
      .addPanel(
        grafana.tablePanel.new(
          'Backups',
          datasource='$datasource',
          span='6',
          sort={
            col: 2,
            desc: false,
          },
          styles=[
            {
              alias: 'Time',
              dateFormat: 'YYYY-MM-DD HH:mm:ss',
              type: 'hidden',
              pattern: 'Time',
            },
            {
              alias: 'Repository',
              pattern: 'repo',
            },
            {
              alias: 'Total Backups',
              pattern: 'Value #A',
              type: 'number',
              unit: 'short',
            },
            {
              alias: 'Last Backup',
              pattern: 'Value #B',
              type: 'number',
              unit: 'dateTimeAsSystem',
              decimals: '0',
            },
            {
              alias: 'Time Since last Backup',
              pattern: 'Value #C',
              type: 'number',
              unit: 'dtdurations',
              decimals: '1',
              colorMode: 'cell',
              colors: [
                'rgba(50, 172, 45, 0.97)',
                'rgba(237, 129, 40, 0.89)',
                'rgba(245, 54, 54, 0.9)',
              ],
              thresholds: [
                std.toString($._config.backupThreshold * 0.75),
                std.toString($._config.backupThreshold),
              ],
            },
          ]
        )
        .addTarget(prometheus.target(totalBackups, format='table', instant=true))
        .addTarget(prometheus.target(lastBackupDate, format='table', instant=true))
        .addTarget(prometheus.target(secondsSinceLastBackup, format='table', instant=true)),
        gridPos={ h: 6, w: 24, x: 0, y: 1 }
      ) + { templating+: { list+: [prometheusTemplate] } },
  },
}
