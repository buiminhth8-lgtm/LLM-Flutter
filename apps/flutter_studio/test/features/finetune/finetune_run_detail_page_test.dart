import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/finetune/finetune_api_client.dart';
import 'package:flutter_studio/features/finetune/finetune_controller.dart';
import 'package:flutter_studio/features/finetune/finetune_run_detail_page.dart';
import 'package:flutter_studio/features/finetune/finetune_state.dart';
import 'package:flutter_studio/features/finetune/models/finetune_checkpoint_dto.dart';
import 'package:flutter_studio/features/finetune/models/finetune_metric_dto.dart';
import 'package:flutter_studio/features/finetune/models/finetune_run_dto.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class DetailHttpClient extends http.BaseClient {
  final List<String> paths = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    paths.add('${request.method} ${request.url.path}');
    Object response = _run(status: 'cancelled');
    if (request.url.path == '/v1/finetune/runs') {
      response = {
        'data': [_run(status: 'cancelled')],
      };
    } else if (request.url.path.endsWith('/metrics')) {
      response = {
        'data': [_metric()],
      };
    } else if (request.url.path.endsWith('/logs')) {
      response = {'data': <Object?>[]};
    } else if (request.url.path.endsWith('/checkpoints')) {
      response = {
        'data': [_checkpoint()],
      };
    } else if (request.url.path.endsWith('/resume')) {
      response = _run(status: 'queued');
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(response))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }

  Map<String, Object?> _run({String status = 'running'}) => {
    'run_id': 'run-1',
    'dataset_version_id': 'dsv-1',
    'recipe_id': 'recipe-1',
    'base_model_id': 'qwen-local',
    'method': 'qlora',
    'adapter_name': 'adapter',
    'adapter_id': status == 'completed' ? 'adapter-1' : null,
    'status': status,
    'config_snapshot': {'method': 'qlora'},
    'dataset_manifest_snapshot': {'dataset_version_id': 'dsv-1'},
    'current_step': 1,
    'total_steps': 3,
    'last_checkpoint_id': 'ckpt-1',
    'cancel_requested': false,
    'created_at': 'now',
    'updated_at': 'now',
  };

  Map<String, Object?> _metric() => {
    'metric_id': 'm1',
    'run_id': 'run-1',
    'step': 1,
    'metric_type': 'train',
    'metrics': {'train_loss': 2.9},
    'created_at': 'now',
  };

  Map<String, Object?> _checkpoint() => {
    'checkpoint_id': 'ckpt-1',
    'run_id': 'run-1',
    'checkpoint_type': 'last',
    'step': 1,
    'checkpoint_path': 'finetune/runs/run-1/checkpoints/last/step-1',
    'is_last': true,
    'created_at': 'now',
  };
}

FinetuneRunDto _run({String status = 'running', String? adapterId}) =>
    FinetuneRunDto.fromMap({
      'run_id': 'run-1',
      'dataset_version_id': 'dsv-1',
      'recipe_id': 'recipe-1',
      'base_model_id': 'qwen-local',
      'method': 'qlora',
      'adapter_name': 'adapter',
      'adapter_id': adapterId,
      'status': status,
      'config_snapshot': {'method': 'qlora'},
      'dataset_manifest_snapshot': {'dataset_version_id': 'dsv-1'},
      'current_step': 1,
      'total_steps': 3,
      'train_loss': 2.9,
      'last_checkpoint_id': 'ckpt-1',
      'cancel_requested': false,
      'created_at': 'now',
      'updated_at': 'now',
    });

void main() {
  testWidgets('Run Detail displays status, metrics, checkpoints and controls', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(1200, 1800));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final httpClient = DetailHttpClient();
    final controller = FinetuneController(
      FinetuneApiClient(
        LlmStudioClient('http://localhost', httpClient: httpClient),
      ),
    );
    controller.state = FinetuneState(
      currentRun: _run(),
      metrics: [
        FinetuneMetricDto.fromMap({
          'metric_id': 'm1',
          'run_id': 'run-1',
          'step': 1,
          'metric_type': 'train',
          'metrics': {'train_loss': 2.9},
          'created_at': 'now',
        }),
      ],
      checkpoints: [
        FinetuneCheckpointDto.fromMap({
          'checkpoint_id': 'ckpt-1',
          'run_id': 'run-1',
          'checkpoint_type': 'last',
          'step': 1,
          'checkpoint_path': 'finetune/runs/run-1/checkpoints/last/step-1',
          'is_last': true,
          'created_at': 'now',
        }),
      ],
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: FinetuneRunDetailPage(
            controller: controller,
            onOpenAdapter: () {},
          ),
        ),
      ),
    );

    expect(find.text('运行中'), findsOneWidget);
    expect(find.text('训练 loss：2.9'), findsOneWidget);
    await tester.ensureVisible(find.textContaining('最近检查点 步数 1'));
    expect(find.textContaining('最近检查点 步数 1'), findsOneWidget);
    expect(find.text('创建评估会话'), findsNothing);
    expect(find.text('与基础模型对比'), findsNothing);

    await tester.tap(find.byKey(const Key('finetune-cancel')));
    await tester.pump();
    expect(httpClient.paths, contains('POST /v1/finetune/runs/run-1/cancel'));

    controller.state = controller.state.copyWith(
      currentRun: _run(status: 'failed'),
    );
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: FinetuneRunDetailPage(
            controller: controller,
            onOpenAdapter: () {},
          ),
        ),
      ),
    );
    await tester.tap(find.byKey(const Key('finetune-resume-last')));
    await tester.pump();
    expect(httpClient.paths, contains('POST /v1/finetune/runs/run-1/resume'));
  });

  testWidgets('Completed run displays adapter result', (tester) async {
    await tester.binding.setSurfaceSize(const Size(1200, 1800));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    var opened = false;
    FinetuneRunDto? evaluationRun;
    final controller = FinetuneController(
      FinetuneApiClient(
        LlmStudioClient('http://localhost', httpClient: DetailHttpClient()),
      ),
    );
    controller.state = FinetuneState(
      currentRun: _run(status: 'completed', adapterId: 'adapter-1'),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: FinetuneRunDetailPage(
            controller: controller,
            onOpenAdapter: () => opened = true,
            onCreateEvaluationSession: (run) => evaluationRun = run,
          ),
        ),
      ),
    );
    await tester.ensureVisible(
      find.byKey(const Key('finetune-create-evaluation-session')),
    );
    await tester.tap(
      find.byKey(const Key('finetune-create-evaluation-session')),
    );
    await tester.pump();

    await tester.ensureVisible(find.byKey(const Key('finetune-open-adapter')));
    await tester.tap(find.byKey(const Key('finetune-open-adapter')));
    await tester.pump();

    expect(find.textContaining('不会自动启用'), findsOneWidget);
    expect(evaluationRun?.runId, 'run-1');
    expect(opened, isTrue);
  });
}
