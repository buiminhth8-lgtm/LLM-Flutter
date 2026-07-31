import 'package:flutter/material.dart';
import 'package:flutter_studio/features/datasets/models/dataset_manifest_dto.dart';
import 'package:flutter_studio/features/datasets/models/dataset_version_dto.dart';
import 'package:flutter_studio/features/datasets/widgets/dataset_manifest_panel.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Manifest Panel displays paths and split summary', (
    tester,
  ) async {
    const version = DatasetVersionDto(
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
    );
    const manifest = DatasetManifestDto(
      datasetVersionId: 'dsv-1',
      datasetId: 'dataset-1',
      version: 1,
      format: 'sft_jsonl',
      split: {'strategy': 'group_by_chapter'},
    );

    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: DatasetManifestPanel(version: version, manifest: manifest),
        ),
      ),
    );

    expect(find.textContaining('manifest.json'), findsOneWidget);
    expect(find.textContaining('group_by_chapter'), findsOneWidget);
  });
}
