class TargetLengthDto {
  const TargetLengthDto({
    this.unit = 'chars',
    this.min = 1200,
    this.max = 1800,
    this.strategy = 'soft',
  });

  factory TargetLengthDto.fromMap(Map<dynamic, dynamic> map) => TargetLengthDto(
    unit: '${map['unit'] ?? 'chars'}',
    min: (map['min'] as num?)?.toInt() ?? 1200,
    max: (map['max'] as num?)?.toInt() ?? 1800,
    strategy: '${map['strategy'] ?? 'soft'}',
  );

  final String unit;
  final int min;
  final int max;
  final String strategy;

  Map<String, Object?> toMap() => {
    'unit': unit,
    'min': min,
    'max': max,
    'strategy': strategy,
  };
}
