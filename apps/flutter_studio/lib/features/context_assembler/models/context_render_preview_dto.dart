import 'context_assembly_result_dto.dart';

class ContextRenderPreviewDto {
  const ContextRenderPreviewDto({
    required this.assembly,
    required this.renderedPrompt,
    required this.missingVariables,
    required this.renderWarnings,
    required this.promptHash,
  });

  factory ContextRenderPreviewDto.fromMap(Map<dynamic, dynamic> map) =>
      ContextRenderPreviewDto(
        assembly: ContextAssemblyResultDto.fromMap(map),
        renderedPrompt: '${map['rendered_prompt'] ?? ''}',
        missingVariables:
            (map['missing_variables'] as List?)
                ?.map((item) => '$item')
                .toList(growable: false) ??
            const [],
        renderWarnings:
            (map['render_warnings'] as List?)
                ?.map((item) => '$item')
                .toList(growable: false) ??
            const [],
        promptHash: '${map['prompt_hash'] ?? ''}',
      );

  final ContextAssemblyResultDto assembly;
  final String renderedPrompt;
  final List<String> missingVariables;
  final List<String> renderWarnings;
  final String promptHash;
}
