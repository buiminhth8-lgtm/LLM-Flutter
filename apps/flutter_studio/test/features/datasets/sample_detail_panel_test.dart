import 'package:flutter/material.dart';
import 'package:flutter_studio/features/datasets/models/training_sample_dto.dart';
import 'package:flutter_studio/features/datasets/widgets/sample_detail_panel.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('sample detail displays fields and approve reject callbacks', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(900, 1200));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    UpdateSampleRequest? saved;
    var approved = false;
    String? rejectedReason;
    const sample = TrainingSampleDto(
      sampleId: 'sample-1',
      datasetId: 'dataset-1',
      sampleType: 'sft',
      instruction: 'inst',
      input: 'input',
      output: 'output',
      sourceHash: 's',
      contentHash: 'c',
      status: 'pending',
      createdAt: 'now',
      updatedAt: 'now',
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SampleDetailPanel(
            sample: sample,
            onSave: (request) => saved = request,
            onApprove: () => approved = true,
            onReject: (reason) => rejectedReason = reason,
          ),
        ),
      ),
    );

    expect(find.text('inst'), findsOneWidget);
    await tester.enterText(
      find.byKey(const Key('sample-output')),
      'better output',
    );
    await tester.ensureVisible(find.byKey(const Key('sample-save')));
    await tester.tap(find.byKey(const Key('sample-save')));
    expect(saved?.output, 'better output');
    await tester.ensureVisible(find.byKey(const Key('sample-approve')));
    await tester.tap(find.byKey(const Key('sample-approve')));
    expect(approved, isTrue);
    await tester.ensureVisible(find.byKey(const Key('sample-reject')));
    await tester.tap(find.byKey(const Key('sample-reject')));
    expect(rejectedReason, isNotNull);
  });
}
