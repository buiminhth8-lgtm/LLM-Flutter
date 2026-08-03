import 'evaluation_case_dto.dart';
import 'evaluation_finding_dto.dart';
import 'evaluation_metric_dto.dart';
import 'evaluation_report_dto.dart';
import 'manual_evaluation_score_dto.dart';

class EvaluationRunDto {
  const EvaluationRunDto({
    required this.runId,
    required this.name,
    required this.targetType,
    required this.targetId,
    required this.status,
    this.description,
    this.projectId,
    this.chapterId,
    this.generationId,
    this.revisionId,
    this.adapterEvalSessionId,
    this.memoryRetrievalId,
    this.evaluatorConfig = const {},
    this.overallScore,
    this.summaryText,
    this.errorCode,
    this.errorMessage,
    this.jobId,
    this.createdBy,
    this.startedAt,
    this.finishedAt,
    this.createdAt,
    this.updatedAt,
    this.cases = const [],
    this.metrics = const [],
    this.findings = const [],
    this.manualScores = const [],
    this.reports = const [],
  });

  final String runId;
  final String name;
  final String? description;
  final String? projectId;
  final String? chapterId;
  final String? generationId;
  final String? revisionId;
  final String? adapterEvalSessionId;
  final String? memoryRetrievalId;
  final String targetType;
  final String targetId;
  final String status;
  final Map<String, dynamic> evaluatorConfig;
  final double? overallScore;
  final String? summaryText;
  final String? errorCode;
  final String? errorMessage;
  final String? jobId;
  final String? createdBy;
  final String? startedAt;
  final String? finishedAt;
  final String? createdAt;
  final String? updatedAt;
  final List<EvaluationCaseDto> cases;
  final List<EvaluationMetricDto> metrics;
  final List<EvaluationFindingDto> findings;
  final List<ManualEvaluationScoreDto> manualScores;
  final List<EvaluationReportDto> reports;

  factory EvaluationRunDto.fromMap(Object? value) {
    final map = Map<String, dynamic>.from((value as Map?) ?? const {});
    final rawScore = map['overall_score'];
    return EvaluationRunDto(
      runId: '${map['run_id'] ?? ''}',
      name: '${map['name'] ?? ''}',
      description: map['description']?.toString(),
      projectId: map['project_id']?.toString(),
      chapterId: map['chapter_id']?.toString(),
      generationId: map['generation_id']?.toString(),
      revisionId: map['revision_id']?.toString(),
      adapterEvalSessionId: map['adapter_eval_session_id']?.toString(),
      memoryRetrievalId: map['memory_retrieval_id']?.toString(),
      targetType: '${map['target_type'] ?? ''}',
      targetId: '${map['target_id'] ?? ''}',
      status: '${map['status'] ?? ''}',
      evaluatorConfig: Map<String, dynamic>.from(
        (map['evaluator_config'] as Map?) ?? const {},
      ),
      overallScore: rawScore is num
          ? rawScore.toDouble()
          : double.tryParse('${rawScore ?? ''}'),
      summaryText: map['summary_text']?.toString(),
      errorCode: map['error_code']?.toString(),
      errorMessage: map['error_message']?.toString(),
      jobId: map['job_id']?.toString(),
      createdBy: map['created_by']?.toString(),
      startedAt: map['started_at']?.toString(),
      finishedAt: map['finished_at']?.toString(),
      createdAt: map['created_at']?.toString(),
      updatedAt: map['updated_at']?.toString(),
      cases: ((map['cases'] as List?) ?? const [])
          .map(EvaluationCaseDto.fromMap)
          .toList(growable: false),
      metrics: ((map['metrics'] as List?) ?? const [])
          .map(EvaluationMetricDto.fromMap)
          .toList(growable: false),
      findings: ((map['findings'] as List?) ?? const [])
          .map(EvaluationFindingDto.fromMap)
          .toList(growable: false),
      manualScores: ((map['manual_scores'] as List?) ?? const [])
          .map(ManualEvaluationScoreDto.fromMap)
          .toList(growable: false),
      reports: ((map['reports'] as List?) ?? const [])
          .map(EvaluationReportDto.fromMap)
          .toList(growable: false),
    );
  }
}
