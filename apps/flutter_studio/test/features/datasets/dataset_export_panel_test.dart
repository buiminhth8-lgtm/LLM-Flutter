import 'package:flutter/material.dart';
import 'package:flutter_studio/features/datasets/models/dataset_export_dto.dart';
import 'package:flutter_studio/features/datasets/widgets/dataset_export_panel.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('dataset export panel calls export API callback', (tester) async {
    var exported = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: DatasetExportPanel(
            exports: const [
              DatasetExportDto(
                exportId: 'export-1',
                datasetId: 'dataset-1',
                format: 'sft_jsonl',
                exportPath: 'datasets/dataset-1/exports/export.jsonl',
                sampleCount: 1,
                approvedOnly: true,
                status: 'created',
                createdAt: 'now',
              ),
            ],
            onExport: () => exported = true,
          ),
        ),
      ),
    );

    expect(find.text('Export SFT JSONL'), findsOneWidget);
    expect(find.textContaining('export.jsonl'), findsOneWidget);
    await tester.tap(find.byKey(const Key('dataset-export-sft')));
    expect(exported, isTrue);
  });
}
