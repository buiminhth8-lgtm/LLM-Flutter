import 'dart:convert';

import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/finetune/finetune_api_client.dart';
import 'package:flutter_studio/features/finetune/models/finetune_create_run_request_dto.dart';
import 'package:flutter_studio/features/finetune/models/finetune_preflight_dto.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class FinetuneApiHttpClient extends http.BaseClient {
  final List<String> paths = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    paths.add('${request.method} ${request.url.path}');
    final path = request.url.path;
    Object response = _run();
    if (path.endsWith('/preflight')) {
      response = {
        'ok': true,
        'errors': <Object?>[],
        'warnings': [
          {'code': 'FINETUNE_NO_VALIDATION_SPLIT'},
        ],
        'resolved_config': {'method': 'qlora'},
      };
    } else if (path == '/v1/finetune/runs') {
      response = request.method == 'POST'
          ? _run(status: 'queued')
          : {
              'data': [_run()],
            };
    } else if (path.endsWith('/start')) {
      response = _run(status: 'queued');
    } else if (path.endsWith('/cancel')) {
      response = _run(status: 'cancelled');
    } else if (path.endsWith('/resume')) {
      response = _run(status: 'queued');
    } else if (path.endsWith('/metrics')) {
      response = {
        'data': [_metric()],
      };
    } else if (path.endsWith('/logs')) {
      response = {
        'data': [_log()],
      };
    } else if (path.endsWith('/checkpoints')) {
      response = {
        'data': [_checkpoint()],
      };
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(response))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }

  Map<String, Object?> _run({String status = 'completed'}) => {
    'run_id': 'run-1',
    'job_id': 'job-1',
    'dataset_version_id': 'dsv-1',
    'recipe_id': 'recipe-1',
    'base_model_id': 'qwen-local',
    'method': 'qlora',
    'adapter_name': 'adapter',
    'adapter_id': 'adapter-1',
    'status': status,
    'config_snapshot': {'method': 'qlora'},
    'dataset_manifest_snapshot': {'dataset_version_id': 'dsv-1'},
    'current_step': 2,
    'total_steps': 3,
    'train_loss': 2.9,
    'val_loss': 3.1,
    'best_val_loss': 3.1,
    'cancel_requested': false,
    'created_at': 'now',
    'updated_at': 'now',
    'metrics': [_metric()],
    'logs': [_log()],
    'checkpoints': [_checkpoint()],
  };

  Map<String, Object?> _metric() => {
    'metric_id': 'metric-1',
    'run_id': 'run-1',
    'step': 1,
    'metric_type': 'train',
    'metrics': {'train_loss': 2.9, 'learning_rate': 0.0002},
    'created_at': 'now',
  };

  Map<String, Object?> _log() => {
    'log_id': 'log-1',
    'run_id': 'run-1',
    'level': 'info',
    'message': 'started',
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

void main() {
  test('FinetuneApiClient parses preflight, run, metrics, logs, checkpoints', () async {
    final httpClient = FinetuneApiHttpClient();
    final api = FinetuneApiClient(
      LlmStudioClient('http://localhost', httpClient: httpClient),
    );

    final preflight = await api.preflightFinetune(
      const FinetunePreflightRequestDto(
        datasetVersionId: 'dsv-1',
        recipeId: 'recipe-1',
        baseModelId: 'qwen-local',
        adapterName: 'adapter',
      ),
    );
    final run = await api.createFinetuneRun(
      const FinetuneCreateRunRequestDto(
        datasetVersionId: 'dsv-1',
        recipeId: 'recipe-1',
        baseModelId: 'qwen-local',
        adapterName: 'adapter',
      ),
    );

    expect(preflight.ok, isTrue);
    expect(preflight.warnings.first['code'], 'FINETUNE_NO_VALIDATION_SPLIT');
    expect(run.status, 'queued');
    expect((await api.listFinetuneRuns()).first.runId, 'run-1');
    expect((await api.getFinetuneMetrics('run-1')).first.trainLoss, 2.9);
    expect((await api.getFinetuneLogs('run-1')).first.message, 'started');
    expect((await api.getFinetuneCheckpoints('run-1')).first.isLast, isTrue);
    await api.startFinetuneRun('run-1');
    await api.cancelFinetuneRun('run-1');
    await api.resumeFinetuneRun('run-1', checkpointId: 'ckpt-1');
    expect(httpClient.paths, contains('POST /v1/finetune/preflight'));
  });
}
