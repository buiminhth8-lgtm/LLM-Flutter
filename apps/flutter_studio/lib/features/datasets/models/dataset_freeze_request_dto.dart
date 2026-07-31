class DatasetFreezeRequestDto {
  const DatasetFreezeRequestDto({
    required this.name,
    this.description,
    this.splitStrategy = 'group_by_chapter',
    this.valRatio = 0.1,
    this.seed = 42,
    this.exactHash = true,
    this.nearDuplicate = true,
    this.nearDuplicateThreshold = 0.92,
    this.exportFormat = 'sft_jsonl',
  });

  final String name;
  final String? description;
  final String splitStrategy;
  final double valRatio;
  final int seed;
  final bool exactHash;
  final bool nearDuplicate;
  final double nearDuplicateThreshold;
  final String exportFormat;

  Map<String, Object?> toMap() => {
    'name': name,
    if (description != null) 'description': description,
    'split': {'strategy': splitStrategy, 'val_ratio': valRatio, 'seed': seed},
    'dedupe': {
      'exact_hash': exactHash,
      'near_duplicate': nearDuplicate,
      'near_duplicate_threshold': nearDuplicateThreshold,
    },
    'export_format': exportFormat,
  };
}
