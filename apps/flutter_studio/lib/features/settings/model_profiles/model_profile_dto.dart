class ModelProfileDto {
  const ModelProfileDto({
    required this.id,
    required this.name,
    required this.provider,
    this.model,
    this.status = 'enabled',
    this.description,
    this.defaultParams = const {},
    this.capabilities = const {},
    this.privacyPolicy = const {},
    this.connection = const {},
    this.metadata = const {},
    this.isDefault = false,
    this.createdAt = '',
    this.updatedAt = '',
  });

  factory ModelProfileDto.fromMap(Map<dynamic, dynamic> map) {
    String? asString(Object? value) => value == null ? null : '$value';
    Map<String, dynamic> asMap(Object? value) {
      if (value is Map) {
        return value.map((key, val) => MapEntry('$key', val));
      }
      return const {};
    }

    return ModelProfileDto(
      id: '${map['id'] ?? ''}',
      name: '${map['name'] ?? ''}',
      provider: '${map['provider'] ?? ''}',
      model: asString(map['model']),
      status: '${map['status'] ?? 'enabled'}',
      description: asString(map['description']),
      defaultParams: asMap(map['default_params']),
      capabilities: asMap(map['capabilities']),
      privacyPolicy: asMap(map['privacy_policy']),
      connection: asMap(map['connection']),
      metadata: asMap(map['metadata']),
      isDefault: map['is_default'] == true,
      createdAt: '${map['created_at'] ?? ''}',
      updatedAt: '${map['updated_at'] ?? ''}',
    );
  }

  final String id;
  final String name;
  final String provider;
  final String? model;
  final String status;
  final String? description;
  final Map<String, dynamic> defaultParams;
  final Map<String, dynamic> capabilities;
  final Map<String, dynamic> privacyPolicy;
  final Map<String, dynamic> connection;
  final Map<String, dynamic> metadata;
  final bool isDefault;
  final String createdAt;
  final String updatedAt;

  bool get isBuiltin => metadata['builtin'] == true;
}
