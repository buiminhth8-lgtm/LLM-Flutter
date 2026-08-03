import 'adapter_eval_case_dto.dart';
import 'adapter_eval_report_dto.dart';

class AdapterEvalSessionDto {
  const AdapterEvalSessionDto({
    required this.sessionId,
    required this.name,
    required this.baseModelId,
    required this.adapterId,
    required this.status,
    this.description,
    this.projectId,
    this.finetuneRunId,
    this.datasetVersionId,
    this.cases = const [],
    this.reports = const [],
    this.stats = const {},
  });

  final String sessionId;
  final String name;
  final String? description;
  final String? projectId;
  final String? finetuneRunId;
  final String? datasetVersionId;
  final String baseModelId;
  final String adapterId;
  final String status;
  final List<AdapterEvalCaseDto> cases;
  final List<AdapterEvalReportDto> reports;
  final Map<String, dynamic> stats;

  factory AdapterEvalSessionDto.fromMap(Object? value) {
    final map = Map<String, dynamic>.from((value as Map?) ?? const {});
    return AdapterEvalSessionDto(
      sessionId: '${map['session_id'] ?? ''}',
      name: '${map['name'] ?? ''}',
      description: map['description']?.toString(),
      projectId: map['project_id']?.toString(),
      finetuneRunId: map['finetune_run_id']?.toString(),
      datasetVersionId: map['dataset_version_id']?.toString(),
      baseModelId: '${map['base_model_id'] ?? ''}',
      adapterId: '${map['adapter_id'] ?? ''}',
      status: '${map['status'] ?? ''}',
      cases: ((map['cases'] as List?) ?? const [])
          .map(AdapterEvalCaseDto.fromMap)
          .toList(growable: false),
      reports: ((map['reports'] as List?) ?? const [])
          .map(AdapterEvalReportDto.fromMap)
          .toList(growable: false),
      stats: Map<String, dynamic>.from((map['stats'] as Map?) ?? const {}),
    );
  }
}
