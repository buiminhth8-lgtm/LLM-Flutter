import 'package:flutter/material.dart';
import 'package:flutter_studio/features/datasets/models/training_sample_dto.dart';
import 'package:flutter_studio/features/datasets/widgets/sample_table.dart';
import 'package:flutter_test/flutter_test.dart';

TrainingSampleDto _sample(String id, String status) => TrainingSampleDto(
  sampleId: id,
  datasetId: 'dataset-1',
  sampleType: 'sft',
  instruction: 'instruction $status',
  input: 'input',
  output: 'output',
  sourceHash: 's$id',
  contentHash: 'c$id',
  status: status,
  createdAt: 'now',
  updatedAt: 'now',
);

void main() {
  testWidgets('sample table displays pending approved rejected samples', (
    tester,
  ) async {
    TrainingSampleDto? selected;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SampleTable(
            samples: [
              _sample('s1', 'pending'),
              _sample('s2', 'approved'),
              _sample('s3', 'rejected'),
            ],
            currentSampleId: null,
            onSelect: (sample) => selected = sample,
          ),
        ),
      ),
    );

    expect(find.text('pending'), findsOneWidget);
    expect(find.text('approved'), findsOneWidget);
    expect(find.text('rejected'), findsOneWidget);
    await tester.tap(find.byKey(const Key('sample-row-s2')));
    expect(selected?.sampleId, 's2');
  });
}
