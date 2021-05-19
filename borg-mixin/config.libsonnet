{
  _config+:: {
    // Selectors are inserted between {} in Prometheus queries.
    borgSelector: 'job="borg-db"',

    // Threshold for when the last backup was specified in seconds
    // Default: 24h + 5 minutes
    backupThreshold: (3600 * 24) + 300,
  },
}
