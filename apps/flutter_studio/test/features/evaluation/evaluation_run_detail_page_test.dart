import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/evaluation/evaluation_api_client.dart';
import 'package:flutter_studio/features/evaluation/evaluation_controller.dart';
import 'package:flutter_studio/features/evaluation/evaluation_run_detail_page.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class EvaluationDetailHttpClient extends http.BaseClient {
  bool manualSaved = false;
  bool reportGenerated = false;
  bool findingUpdated = false;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path;
    Object body = _run();
    if (path == '/v1/evaluation/runs') {
      body = {
        'data': [_run()],
      };
    } else if (path.endsWith('/metrics')) {
      body = {
        'data': [_metric()],
      };
    } else if (path.endsWith('/findings')) {
      body = {
        'data': [_finding()],
      };
    } else if (path.contains('/findings/')) {
      findingUpdated = true;
      body = _finding(status: 'resolved');
    } else if (path.endsWith('/manual-score')) {
      manualSaved = true;
      body = _manualScore();
    } else if (path.endsWith('/manual-scores')) {
      body = {
        'data': [_manualScore()],
      };
    } else if (path.endsWith('/report')) {
      reportGenerated = true;
      body = _report();
    } else if (path.endsWith('/reports')) {
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
    'name': 'Chapter evaluation',
    'target_type': 'chapter',
    'target_id': 'c1',
    'status': 'completed',
    'overall_score': 4,
    'summary_text': 'complete',
    'evaluator_config': {
      'enabled_evaluators': ['repetition'],
    },
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
  };

  Map<String, Object?> _finding({String status = 'open'}) => {
    'finding_id': 'finding-1',
    'run_id': 'eval-1',
    'severity': 'warning',
    'category': 'repetition',
    'title': 'Repeated sentence',
    'message': 'A sentence repeats.',
    'evidence': {'count': 2},
    'status': status,
  };

  Map<String, Object?> _manualScore() => {
    'manual_score_id': 'manual-1',
    'run_id': 'eval-1',
    'target_type': 'chapter',
    'target_id': 'c1',
    'overall_score': 4,
    'dimensions': {'style': 4},
    'notes': 'manual note',
  };

  Map<String, Object?> _report() => {
    'report_id': 'report-1',
    'run_id': 'eval-1',
    'report_type': 'chapter_evaluation',
    'summary_text': 'report summary',
    'report': {
      'summary': {'overall_score': 4},
      'metrics': [],
      'findings': [],
      'manual_evaluation': [],
      'limitations': ['advisory only'],
    },
  };
}

void main() {
  testWidgets(
    'run detail displays metrics, findings, manual score and report',
    (tester) async {
      await tester.binding.setSurfaceSize(const Size(1600, 1000));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      final httpClient = EvaluationDetailHttpClient();
      final controller = EvaluationController(
        EvaluationApiClient(
          LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient),
        ),
      );
      addTearDown(controller.dispose);
      await controller.refresh();
      await controller.selectRun('eval-1');

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(body: EvaluationRunDetailPage(controller: controller)),
        ),
      );

      expect(find.text('repetition_score'), findsOneWidget);
      expect(find.text('Repeated sentence'), findsOneWidget);
      await tester.enterText(
        find.byKey(const Key('evaluation-manual-notes')),
        'manual note',
      );
      await tester.tap(find.byKey(const Key('evaluation-save-manual-score')));
      await tester.pumpAndSettle();
      expect(httpClient.manualSaved, isTrue);

      await tester.tap(find.byKey(const Key('evaluation-generate-report')));
      await tester.pumpAndSettle();
      expect(httpClient.reportGenerated, isTrue);
    },
  );
}
