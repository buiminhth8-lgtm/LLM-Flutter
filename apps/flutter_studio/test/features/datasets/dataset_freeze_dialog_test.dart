import 'package:flutter/material.dart';
import 'package:flutter_studio/features/datasets/models/dataset_freeze_request_dto.dart';
import 'package:flutter_studio/features/datasets/widgets/dataset_freeze_dialog.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Freeze Dialog submits freeze request', (tester) async {
    DatasetFreezeRequestDto? submitted;
    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => Scaffold(
            body: TextButton(
              onPressed: () async {
                submitted = await showDialog<DatasetFreezeRequestDto>(
                  context: context,
                  builder: (_) => const DatasetFreezeDialog(defaultName: 'v1'),
                );
              },
              child: const Text('open'),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('dataset-freeze-name')),
      'Frozen v1',
    );
    await tester.tap(find.byKey(const Key('dataset-freeze-submit')));
    await tester.pumpAndSettle();

    expect(submitted?.name, 'Frozen v1');
    expect(submitted?.splitStrategy, 'group_by_chapter');
  });
}
