import 'package:flutter/material.dart';
import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/datasets/dataset_api_client.dart';
import 'package:flutter_studio/features/datasets/dataset_controller.dart';
import 'package:flutter_studio/features/datasets/dataset_state.dart';
import 'package:flutter_studio/features/datasets/dataset_version_page.dart';
import 'package:flutter_studio/features/datasets/models/dataset_manifest_dto.dart';
import 'package:flutter_studio/features/datasets/models/dataset_version_dto.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('DatasetVersion page displays frozen version details', (
    tester,
  ) async {
    final controller = DatasetController(
      DatasetApiClient(LlmStudioClient('http://127.0.0.1:8000')),
    );
    addTearDown(controller.dispose);
    controller.state = const DatasetState(
      currentVersion: DatasetVersionDto(
        datasetVersionId: 'dsv-1',
        datasetId: 'dataset-1',
        version: 1,
        name: 'v1',
        status: 'frozen',
        sourceSampleCount: 1,
        trainSampleCount: 1,
        valSampleCount: 0,
        rejectedDuplicateCount: 0,
        warningCount: 0,
        trainCharCount: 10,
        valCharCount: 0,
        trainTokenEstimate: 10,
        valTokenEstimate: 0,
        contentHash: 'hash',
        manifestPath: 'datasets/dataset-1/versions/v1/manifest.json',
        trainPath: 'datasets/dataset-1/versions/v1/train.jsonl',
        createdAt: 'now',
      ),
      currentManifest: DatasetManifestDto(
        datasetVersionId: 'dsv-1',
        datasetId: 'dataset-1',
        version: 1,
        format: 'sft_jsonl',
      ),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: DatasetVersionPage(controller: controller)),
      ),
    );

    expect(find.textContaining('数据集版本'), findsOneWidget);
    expect(find.textContaining('v1'), findsWidgets);
  });
}
