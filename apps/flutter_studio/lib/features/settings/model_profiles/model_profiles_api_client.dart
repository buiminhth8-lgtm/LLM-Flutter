import '../../../core/api/api_client.dart';
import 'model_profile_dto.dart';

class ModelProfilesApiClient {
  ModelProfilesApiClient(this._client);

  final LlmStudioClient _client;

  Future<List<ModelProfileDto>> listProfiles({
    String? provider,
    String? status,
  }) async {
    final items = await _client.modelProfiles(
      provider: provider,
      status: status,
    );
    return items
        .whereType<Map>()
        .map((item) => ModelProfileDto.fromMap(item))
        .toList();
  }

  Future<Map<String, dynamic>> ensureDefaults() async {
    return _client.ensureModelProfileDefaults();
  }

  Future<ModelProfileDto?> getDefault() async {
    final item = await _client.defaultModelProfile();
    return item == null ? null : ModelProfileDto.fromMap(item);
  }
}
