import 'dart:convert';

import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/evaluation/evaluation_api_client.dart';
import 'package:flutter_studio/features/evaluation/models/evaluation_run_dto.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class EvaluationApiHttpClient extends http.BaseClient {
  final requests = <String>[];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    requests.add('${request.method} ${request.url.path}');
    Object body = _run();
    if (request.url.path == '/v1/evaluation/runs' && request.method == 'GET') {
      body = {
        'data': [_run()],
      };
    } else if (request.url.path.endsWith('/metrics')) {
      body = {
        'data': [_metric()],
      };
    } else if (request.url.path.endsWith('/findings')) {
      body = {
        'data': [_finding()],
      };
    } else if (request.url.path.endsWith('/manual-score')) {
      body = _manualScore();
    } else if (request.url.path.endsWith('/manual-scores')) {
      body = {
        'data': [_manualScore()],
      };
    } else if (request.url.path.endsWith('/report')) {
      body = _report();
    } else if (request.url.path.endsWith('/reports')) {
      body = {
        'data': [_report()],
      };
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(body))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }

  Map<String, Object?> _run() => {
    'run_id': 'eval-1',
    'name': 'Stage 11 run',
    'project_id': 'p1',
    'chapter_id': 'c1',
    'target_type': 'chapter',
    'target_id': 'c1',
    'status': 'completed',
    'evaluator_config': {
      'enabled_evaluators': ['repetition'],
    },
    'overall_score': 4.2,
    'summary_text': 'good',
    'cases': [
      {
        'case_id': 'case-1',
        'run_id': 'eval-1',
        'target_type': 'chapter',
        'target_id': 'c1',
        'evaluator_type': 'repetition',
        'input_snapshot': <String, Object?>{},
        'status': 'completed',
      },
    ],
    'metrics': [_metric()],
    'findings': [_finding()],
    'manual_scores': [_manualScore()],
    'reports': [_report()],
  };

  Map<String, Object?> _metric() => {
    'metric_id': 'metric-1',
    'run_id': 'eval-1',
    'metric_name': 'repetition_score',
    'metric_value': 4.5,
    'metric_unit': 'score',
    'metric': {'source': 'automatic'},
  };

  Map<String, Object?> _finding() => {
    'finding_id': 'finding-1',
    'run_id': 'eval-1',
    'severity': 'warning',
    'category': 'repetition',
    'title': 'Repeated sentence',
    'message': 'A sentence repeats.',
    'evidence': {'count': 2},
    'status': 'open',
  };

  Map<String, Object?> _manualScore() => {
    'manual_score_id': 'manual-1',
    'run_id': 'eval-1',
    'target_type': 'chapter',
    'target_id': 'c1',
    'reviewer_id': 'human',
    'overall_score': 4,
    'dimensions': {'style': 4},
    'notes': 'works',
  };

  Map<String, Object?> _report() => {
    'report_id': 'report-1',
    'run_id': 'eval-1',
    'report_type': 'chapter_evaluation',
    'summary_text': 'report summary',
    'report': {
      'summary': {'overall_score': 4.2},
      'metrics': [],
      'findings': [],
      'manual_evaluation': [],
      'limitations': ['advisory'],
    },
  };
}

void main() {
  test('DTO parses full evaluation run payload', () {
    final dto = EvaluationRunDto.fromMap(EvaluationApiHttpClient()._run());
    expect(dto.runId, 'eval-1');
    expect(dto.cases.single.evaluatorType, 'repetition');
    expect(dto.metrics.single.metricName, 'repetition_score');
    expect(dto.findings.single.title, 'Repeated sentence');
    expect(dto.manualScores.single.overallScore, 4);
    expect(dto.reports.single.reportId, 'report-1');
  });

  test('Evaluation API client maps endpoints', () async {
    final httpClient = EvaluationApiHttpClient();
    final api = EvaluationApiClient(
      LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient),
    );

    final created = await api.createRun(
      const CreateEvaluationRunRequest(
        name: 'run',
        targetType: 'chapter',
        targetId: 'c1',
      ),
    );
    final runs = await api.listRuns(projectId: 'p1');
    final metrics = await api.listMetrics(created.runId);
    final findings = await api.listFindings(created.runId);
    final manual = await api.addManualScore(
      created.runId,
      const ManualEvaluationScoreRequest(overallScore: 4),
    );
    final report = await api.generateReport(created.runId);

    expect(runs.single.runId, 'eval-1');
    expect(metrics.single.metricName, 'repetition_score');
    expect(findings.single.findingId, 'finding-1');
    expect(manual.manualScoreId, 'manual-1');
    expect(report.reportId, 'report-1');
    expect(httpClient.requests, contains('POST /v1/evaluation/runs'));
  });
}
