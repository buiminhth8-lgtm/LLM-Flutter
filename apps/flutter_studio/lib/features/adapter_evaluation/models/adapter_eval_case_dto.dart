import 'adapter_eval_result_dto.dart';
import 'adapter_eval_score_dto.dart';

class AdapterEvalCaseDto {
  const AdapterEvalCaseDto({
    required this.caseId,
    required this.sessionId,
    required this.title,
    required this.mode,
    required this.status,
    this.projectId,
    this.chapterId,
    this.templateId,
    this.promptRendered,
    this.contextSnapshot = const {},
    this.generationParams = const {},
    this.targetLength = const {},
    this.results = const [],
    this.score,
  });

  final String caseId;
  final String sessionId;
  final String title;
  final String mode;
  final String status;
  final String? projectId;
  final String? chapterId;
  final String? templateId;
  final String? promptRendered;
  final Map<String, dynamic> contextSnapshot;
  final Map<String, dynamic> generationParams;
  final Map<String, dynamic> targetLength;
  final List<AdapterEvalResultDto> results;
  final AdapterEvalScoreDto? score;

  factory AdapterEvalCaseDto.fromMap(Object? value) {
    final map = Map<String, dynamic>.from((value as Map?) ?? const {});
    return AdapterEvalCaseDto(
      caseId: '${map['case_id'] ?? ''}',
      sessionId: '${map['session_id'] ?? ''}',
      title: '${map['title'] ?? ''}',
      mode: '${map['mode'] ?? ''}',
      status: '${map['status'] ?? ''}',
      projectId: map['project_id']?.toString(),
      chapterId: map['chapter_id']?.toString(),
      templateId: map['template_id']?.toString(),
      promptRendered: map['prompt_rendered']?.toString(),
      contextSnapshot: Map<String, dynamic>.from(
        (map['context_snapshot'] as Map?) ?? const {},
      ),
      generationParams: Map<String, dynamic>.from(
        (map['generation_params'] as Map?) ?? const {},
      ),
      targetLength: Map<String, dynamic>.from(
        (map['target_length'] as Map?) ?? const {},
      ),
      results: ((map['results'] as List?) ?? const [])
          .map(AdapterEvalResultDto.fromMap)
          .toList(growable: false),
      score: map['score'] is Map
          ? AdapterEvalScoreDto.fromMap(map['score'])
          : null,
    );
  }
}
