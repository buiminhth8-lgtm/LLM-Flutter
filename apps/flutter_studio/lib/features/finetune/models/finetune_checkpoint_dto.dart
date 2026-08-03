class FinetuneCheckpointDto {
  const FinetuneCheckpointDto({
    required this.checkpointId,
    required this.runId,
    required this.checkpointType,
    required this.step,
    required this.checkpointPath,
    required this.createdAt,
    this.epoch,
    this.trainLoss,
    this.valLoss,
    this.checkpointHash,
    this.sizeBytes,
    this.isBest = false,
    this.isLast = false,
  });

  factory FinetuneCheckpointDto.fromMap(Map<dynamic, dynamic> map) =>
      FinetuneCheckpointDto(
        checkpointId: '${map['checkpoint_id'] ?? map['id'] ?? ''}',
        runId: '${map['run_id'] ?? ''}',
        checkpointType: '${map['checkpoint_type'] ?? ''}',
        step: (map['step'] as num?)?.toInt() ?? 0,
        epoch: (map['epoch'] as num?)?.toDouble(),
        trainLoss: (map['train_loss'] as num?)?.toDouble(),
        valLoss: (map['val_loss'] as num?)?.toDouble(),
        checkpointPath: '${map['checkpoint_path'] ?? ''}',
        checkpointHash: map['checkpoint_hash'] == null
            ? null
            : '${map['checkpoint_hash']}',
        sizeBytes: (map['size_bytes'] as num?)?.toInt(),
        isBest: map['is_best'] == true,
        isLast: map['is_last'] == true,
        createdAt: '${map['created_at'] ?? ''}',
      );

  final String checkpointId;
  final String runId;
  final String checkpointType;
  final int step;
  final double? epoch;
  final double? trainLoss;
  final double? valLoss;
  final String checkpointPath;
  final String? checkpointHash;
  final int? sizeBytes;
  final bool isBest;
  final bool isLast;
  final String createdAt;
}
