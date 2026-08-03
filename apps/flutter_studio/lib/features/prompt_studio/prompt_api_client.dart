import 'dart:convert';

import '../../core/api/api_client.dart';
import 'models/prompt_render_result_dto.dart';
import 'models/prompt_template_dto.dart';
import 'models/prompt_template_version_dto.dart';

class PromptApiClient {
  PromptApiClient(this._client);

  final LlmStudioClient _client;

  Future<List<PromptTemplateDto>> listTemplates({
    String? type,
    String? scope,
    String? projectId,
  }) async {
    final items = await _client.promptTemplates(
      type: type,
      scope: scope,
      projectId: projectId,
    );
    return items
        .whereType<Map>()
        .map((item) => PromptTemplateDto.fromMap(item))
        .toList();
  }

  Future<PromptTemplateDto> createTemplate({
    required String name,
    required String type,
    required String instructionTemplate,
    String scope = 'global',
    String? description,
    String? projectId,
    String? systemPrompt,
    String? rolePrompt,
    String? negativePrompt,
    String? outputConstraints,
    required Map<String, dynamic> variablesSchema,
    required Map<String, dynamic> defaultValues,
    String? changeNote,
  }) async {
    final body = await _client.createPromptTemplate({
      'name': name,
      'type': type,
      'scope': scope,
      'instruction_template': instructionTemplate,
      if (description != null && description.isNotEmpty)
        'description': description,
      if (projectId != null && projectId.isNotEmpty) 'project_id': projectId,
      if (systemPrompt != null && systemPrompt.isNotEmpty)
        'system_prompt': systemPrompt,
      if (rolePrompt != null && rolePrompt.isNotEmpty)
        'role_prompt': rolePrompt,
      if (negativePrompt != null && negativePrompt.isNotEmpty)
        'negative_prompt': negativePrompt,
      if (outputConstraints != null && outputConstraints.isNotEmpty)
        'output_constraints': outputConstraints,
      'variables_schema': variablesSchema,
      'default_values': defaultValues,
      if (changeNote != null && changeNote.isNotEmpty)
        'change_note': changeNote,
    });
    return PromptTemplateDto.fromMap(body);
  }

  Future<List<PromptTemplateVersionDto>> listVersions(String templateId) async {
    final items = await _client.promptTemplateVersions(templateId);
    return items
        .whereType<Map>()
        .map((item) => PromptTemplateVersionDto.fromMap(item))
        .toList();
  }

  Future<PromptTemplateVersionDto> createVersion(
    String templateId,
    Map<String, Object?> body,
  ) async {
    final item = await _client.createPromptTemplateVersion(templateId, body);
    return PromptTemplateVersionDto.fromMap(item);
  }

  Future<PromptTemplateDto> activateVersion(
    String templateId,
    String versionId,
  ) async {
    final item = await _client.activatePromptTemplateVersion(
      templateId,
      versionId,
    );
    return PromptTemplateDto.fromMap(item);
  }

  Future<PromptRenderResultDto> render({
    required String templateId,
    String? templateVersionId,
    String? projectId,
    String? chapterId,
    required Map<String, dynamic> variables,
    bool saveRecord = true,
  }) async {
    final item = await _client.renderPrompt({
      'template_id': templateId,
      if (templateVersionId != null && templateVersionId.isNotEmpty)
        'template_version_id': templateVersionId,
      if (projectId != null && projectId.isNotEmpty) 'project_id': projectId,
      if (chapterId != null && chapterId.isNotEmpty) 'chapter_id': chapterId,
      'variables': variables,
      'save_record': saveRecord,
    });
    return PromptRenderResultDto.fromMap(item);
  }

  Future<Map<String, dynamic>> ensureDefaults() async {
    return _client.ensureDefaultPromptTemplates();
  }

  static Map<String, dynamic>? parseJsonObject(String text) {
    final trimmed = text.trim();
    if (trimmed.isEmpty) {
      return const {};
    }
    final decoded = jsonDecode(trimmed);
    if (decoded is Map) {
      return decoded.map((key, value) => MapEntry('$key', value));
    }
    return null;
  }
}
