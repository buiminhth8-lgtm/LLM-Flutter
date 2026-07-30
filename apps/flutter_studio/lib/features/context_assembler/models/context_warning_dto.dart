class ContextWarningDto {
  const ContextWarningDto({
    required this.code,
    required this.message,
    this.affected = const [],
  });

  factory ContextWarningDto.fromMap(Map<dynamic, dynamic> map) =>
      ContextWarningDto(
        code: '${map['code'] ?? ''}',
        message: '${map['message'] ?? ''}',
        affected:
            (map['affected'] as List?)
                ?.map((item) => '$item')
                .toList(growable: false) ??
            const [],
      );

  final String code;
  final String message;
  final List<String> affected;
}
