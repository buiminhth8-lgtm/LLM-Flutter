import 'package:flutter/material.dart';
import 'package:flutter_studio/features/finetune/models/finetune_create_run_request_dto.dart';
import 'package:flutter_studio/features/finetune/models/finetune_preflight_dto.dart';
import 'package:flutter_studio/features/finetune/widgets/finetune_create_run_dialog.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Create Run dialog disables create when preflight has errors', (
    tester,
  ) async {
    FinetunePreflightRequestDto? preflightRequest;
    FinetuneCreateRunRequestDto? createRequest;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: FinetuneCreateRunDialog(
            preflight: const FinetunePreflightDto(
              ok: false,
              errors: [
                {'code': 'FINETUNE_GPU_NOT_AVAILABLE'},
              ],
            ),
            onPreflight: (value) => preflightRequest = value,
            onCreate: (value) => createRequest = value,
          ),
        ),
      ),
    );

    await tester.enterText(
      find.byKey(const Key('finetune-dataset-version')),
      'dsv-1',
    );
    await tester.enterText(find.byKey(const Key('finetune-recipe')), 'recipe-1');
    await tester.tap(find.byKey(const Key('finetune-preflight')));
    await tester.pump();

    expect(preflightRequest?.datasetVersionId, 'dsv-1');
    expect(tester.widget<FilledButton>(find.byKey(const Key('finetune-create-run'))).onPressed, isNull);
    expect(createRequest, isNull);
  });

  testWidgets('Create Run dialog submits after preflight passes', (tester) async {
    FinetuneCreateRunRequestDto? createRequest;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: FinetuneCreateRunDialog(
            preflight: const FinetunePreflightDto(ok: true),
            onPreflight: (_) {},
            onCreate: (value) => createRequest = value,
          ),
        ),
      ),
    );

    await tester.enterText(
      find.byKey(const Key('finetune-dataset-version')),
      'dsv-1',
    );
    await tester.enterText(find.byKey(const Key('finetune-recipe')), 'recipe-1');
    await tester.tap(find.byKey(const Key('finetune-create-run')));
    await tester.pump();

    expect(createRequest?.datasetVersionId, 'dsv-1');
    expect(createRequest?.recipeId, 'recipe-1');
  });
}
