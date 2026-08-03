class FinetuneMetricDto {
  const FinetuneMetricDto({
    required this.metricId,
    required this.runId,
    required this.step,
    required this.metricType,
    required this.metrics,
    required this.createdAt,
    this.epoch,
  });

  factory FinetuneMetricDto.fromMap(Map<dynamic, dynamic> map) =>
      FinetuneMetricDto(
        metricId: '${map['metric_id'] ?? map['id'] ?? ''}',
        runId: '${map['run_id'] ?? ''}',
        step: (map['step'] as num?)?.toInt() ?? 0,
        epoch: (map['epoch'] as num?)?.toDouble(),
        metricType: '${map['metric_type'] ?? map['type'] ?? ''}',
        metrics: _map(map['metrics']),
        createdAt: '${map['created_at'] ?? ''}',
      );

  final String metricId;
  final String runId;
  final int step;
  final double? epoch;
  final String metricType;
  final Map<String, dynamic> metrics;
  final String createdAt;

  double? get trainLoss => (metrics['train_loss'] as num?)?.toDouble();
  double? get valLoss => (metrics['val_loss'] as num?)?.toDouble();
}

Map<String, dynamic> _map(Object? value) {
  if (value is! Map) {
    return const {};
  }
  return value.map((key, value) => MapEntry('$key', value));
}
