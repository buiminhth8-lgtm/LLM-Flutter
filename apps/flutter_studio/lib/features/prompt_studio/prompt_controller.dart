import 'package:flutter/foundation.dart';

import '../../core/api/api_exception.dart';
import 'prompt_api_client.dart';
import 'prompt_state.dart';

class PromptController extends ChangeNotifier {
  PromptController(this._api);

  final PromptApiClient _api;
  PromptState state = const PromptState();

  Future<void> refresh() async {
    state = state.copyWith(loading: true, clearError: true);
    notifyListeners();
    try {
      final templates = await _api.listTemplates();
      final selected =
          state.selectedTemplateId ??
          (templates.isEmpty ? null : templates.first.id);
      state = state.copyWith(
        templates: templates,
        selectedTemplateId: selected,
        loading: false,
        clearError: true,
      );
      if (selected != null) {
        await selectTemplate(selected);
      }
    } catch (error) {
      state = state.copyWith(loading: false, error: _message(error));
      notifyListeners();
    }
  }

  Future<void> ensureDefaults() async {
    try {
      await _api.ensureDefaults();
      await refresh();
    } catch (error) {
      state = state.copyWith(error: _message(error));
      notifyListeners();
    }
  }

  Future<void> selectTemplate(String templateId) async {
    state = state.copyWith(selectedTemplateId: templateId, clearError: true);
    notifyListeners();
    try {
      final versions = await _api.listVersions(templateId);
      state = state.copyWith(versions: versions, clearError: true);
      notifyListeners();
    } catch (error) {
      state = state.copyWith(error: _message(error));
      notifyListeners();
    }
  }

  Future<void> createTemplate({
    required String name,
    required String type,
    required String instructionTemplate,
    required String variablesSchemaJson,
    required String defaultValuesJson,
    String? description,
  }) async {
    try {
      final schema = PromptApiClient.parseJsonObject(variablesSchemaJson);
      final defaults = PromptApiClient.parseJsonObject(defaultValuesJson);
      if (schema == null || defaults == null) {
        state = state.copyWith(
          error: 'variables_schema 和 default_values 必须是 JSON object。',
        );
        notifyListeners();
        return;
      }
      final template = await _api.createTemplate(
        name: name,
        type: type,
        description: description,
        instructionTemplate: instructionTemplate,
        variablesSchema: schema,
        defaultValues: defaults,
      );
      await refresh();
      await selectTemplate(template.id);
    } catch (error) {
      state = state.copyWith(error: _message(error));
      notifyListeners();
    }
  }

  Future<void> renderPreview({
    required String variablesJson,
    String? projectId,
    String? chapterId,
  }) async {
    final selected = state.selectedTemplate;
    if (selected == null) {
      return;
    }
    try {
      final variables = PromptApiClient.parseJsonObject(variablesJson);
      if (variables == null) {
        state = state.copyWith(error: '变量 JSON 必须是 object。');
        notifyListeners();
        return;
      }
      final result = await _api.render(
        templateId: selected.id,
        projectId: projectId,
        chapterId: chapterId,
        variables: variables,
      );
      state = state.copyWith(renderResult: result, clearError: true);
      notifyListeners();
    } catch (error) {
      state = state.copyWith(error: _message(error));
      notifyListeners();
    }
  }

  bool isValidJsonObject(String text) {
    try {
      return PromptApiClient.parseJsonObject(text) != null;
    } on FormatException {
      return false;
    }
  }

  String _message(Object error) {
    if (error is StudioApiException) {
      return error.message;
    }
    return '$error';
  }
}
