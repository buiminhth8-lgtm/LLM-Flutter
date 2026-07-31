import 'dart:convert';

import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/datasets/dataset_api_client.dart';
import 'package:flutter_studio/features/datasets/models/dataset_export_dto.dart';
import 'package:flutter_studio/features/datasets/models/training_dataset_dto.dart';
import 'package:flutter_studio/features/datasets/models/training_sample_dto.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class DatasetApiHttpClient extends http.BaseClient {
  final List<String> paths = [];
  bool exported = false;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    paths.add('${request.method} ${request.url.path}');
    final path = request.url.path;
    Object response = _dataset();
    if (path == '/v1/datasets') {
      response = request.method == 'POST'
          ? _dataset(name: 'created')
          : {
              'data': [_dataset()],
            };
    } else if (path.endsWith('/samples/from-revision')) {
      response = _sample();
    } else if (path.endsWith('/samples/bulk-from-revisions')) {
      response = {
        'created_count': 1,
        'error_count': 0,
        'samples': [_sample()],
        'errors': <Object?>[],
      };
    } else if (path.endsWith('/samples')) {
      response = {
        'data': [_sample()],
      };
    } else if (path.contains('/samples/sample-1/approve')) {
      response = _sample(status: 'approved');
    } else if (path.contains('/samples/sample-1/reject')) {
      response = _sample(status: 'rejected');
    } else if (path.contains('/samples/sample-1')) {
      response = _sample(
        instruction: request.method == 'PATCH' ? 'saved' : 'inst',
      );
    } else if (path.endsWith('/export')) {
      exported = true;
      response = _export();
    } else if (path.endsWith('/exports')) {
      response = {
        'data': [_export()],
      };
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(response))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }

  Map<String, Object?> _dataset({String name = 'dataset'}) => {
    'dataset_id': 'dataset-1',
    'name': name,
    'type': 'sft',
    'status': 'draft',
    'sample_count': 1,
    'approved_sample_count': 0,
    'rejected_sample_count': 0,
    'metadata': <String, Object?>{},
    'created_at': 'now',
    'updated_at': 'now',
  };

  Map<String, Object?> _sample({
    String instruction = 'inst',
    String status = 'pending',
  }) => {
    'sample_id': 'sample-1',
    'dataset_id': 'dataset-1',
    'revision_id': 'rev-1',
    'sample_type': 'sft',
    'instruction': instruction,
    'input': 'input',
    'output': 'output',
    'metadata': <String, Object?>{},
    'source_hash': 'source',
    'content_hash': 'content',
    'quality_score': 4,
    'status': status,
    'created_at': 'now',
    'updated_at': 'now',
  };

  Map<String, Object?> _export() => {
    'export_id': 'export-1',
    'dataset_id': 'dataset-1',
    'format': 'sft_jsonl',
    'export_path': 'datasets/dataset-1/exports/export.jsonl',
    'sample_count': 1,
    'approved_only': true,
    'export_hash': 'hash',
    'status': 'created',
    'created_at': 'now',
  };
}

void main() {
  test('Dataset DTOs parse dataset, sample and export', () {
    final dataset = TrainingDatasetDto.fromMap({
      'id': 'dataset-1',
      'name': 'D',
      'type': 'sft',
      'status': 'draft',
      'sample_count': 2,
      'approved_sample_count': 1,
      'rejected_sample_count': 1,
      'created_at': 'now',
      'updated_at': 'now',
    });
    final sample = TrainingSampleDto.fromMap({
      'id': 'sample-1',
      'dataset_id': 'dataset-1',
      'sample_type': 'sft',
      'instruction': 'inst',
      'input': 'input',
      'output': 'output',
      'source_hash': 's',
      'content_hash': 'c',
      'status': 'approved',
      'created_at': 'now',
      'updated_at': 'now',
    });
    final export = DatasetExportDto.fromMap({
      'id': 'export-1',
      'dataset_id': 'dataset-1',
      'format': 'sft_jsonl',
      'export_path': 'datasets/dataset-1/export.jsonl',
      'sample_count': 1,
      'approved_only': 1,
      'status': 'created',
      'created_at': 'now',
    });

    expect(dataset.datasetId, 'dataset-1');
    expect(sample.status, 'approved');
    expect(export.approvedOnly, isTrue);
  });

  test('Dataset API client calls CRUD, sample and export methods', () async {
    final httpClient = DatasetApiHttpClient();
    final api = DatasetApiClient(
      LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient),
    );

    final created = await api.createDataset(
      const CreateDatasetRequest(name: 'created'),
    );
    final listed = await api.listDatasets();
    final sample = await api.createSampleFromRevision(
      datasetId: 'dataset-1',
      revisionId: 'rev-1',
    );
    final bulk = await api.bulkCreateSamplesFromRevisions(
      datasetId: 'dataset-1',
      minScore: 4,
    );
    final saved = await api.updateSample(
      'sample-1',
      const UpdateSampleRequest(instruction: 'saved'),
    );
    final export = await api.exportDataset(datasetId: 'dataset-1');

    expect(created.name, 'created');
    expect(listed.single.datasetId, 'dataset-1');
    expect(sample.revisionId, 'rev-1');
    expect(bulk.createdCount, 1);
    expect(saved.instruction, 'saved');
    expect(export.exportPath, contains('datasets/dataset-1'));
    expect(httpClient.exported, isTrue);
  });
}
