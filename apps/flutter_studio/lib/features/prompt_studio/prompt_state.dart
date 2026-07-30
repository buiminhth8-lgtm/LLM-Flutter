import 'models/prompt_render_result_dto.dart';
import 'models/prompt_template_dto.dart';
import 'models/prompt_template_version_dto.dart';

class PromptState {
  const PromptState({
    this.templates = const [],
    this.versions = const [],
    this.selectedTemplateId,
    this.renderResult,
    this.loading = false,
    this.error,
  });

  final List<PromptTemplateDto> templates;
  final List<PromptTemplateVersionDto> versions;
  final String? selectedTemplateId;
  final PromptRenderResultDto? renderResult;
  final bool loading;
  final String? error;

  PromptTemplateDto? get selectedTemplate {
    for (final template in templates) {
      if (template.id == selectedTemplateId) {
        return template;
      }
    }
    return templates.isEmpty ? null : templates.first;
  }

  PromptState copyWith({
    List<PromptTemplateDto>? templates,
    List<PromptTemplateVersionDto>? versions,
    String? selectedTemplateId,
    PromptRenderResultDto? renderResult,
    bool? loading,
    String? error,
    bool clearError = false,
  }) {
    return PromptState(
      templates: templates ?? this.templates,
      versions: versions ?? this.versions,
      selectedTemplateId: selectedTemplateId ?? this.selectedTemplateId,
      renderResult: renderResult ?? this.renderResult,
      loading: loading ?? this.loading,
      error: clearError ? null : error ?? this.error,
    );
  }
}
