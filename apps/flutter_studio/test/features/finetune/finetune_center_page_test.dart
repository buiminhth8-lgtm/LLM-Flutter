import 'package:flutter/material.dart';
import 'package:flutter_studio/app/app_routes.dart';
import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/finetune/finetune_api_client.dart';
import 'package:flutter_studio/features/finetune/finetune_center_page.dart';
import 'package:flutter_studio/features/finetune/finetune_controller.dart';
import 'package:flutter_studio/features/finetune/finetune_state.dart';
import 'package:flutter_studio/features/finetune/models/finetune_run_dto.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Fine-tune Center displays run list and create entry', (
    tester,
  ) async {
    final controller = FinetuneController(
      FinetuneApiClient(LlmStudioClient('http://localhost')),
    );
    controller.state = FinetuneState(
      runs: [
        FinetuneRunDto.fromMap({
          'run_id': 'run-1',
          'dataset_version_id': 'dsv-1',
          'recipe_id': 'recipe-1',
          'base_model_id': 'qwen-local',
          'method': 'qlora',
          'adapter_name': 'adapter',
          'status': 'completed',
          'config_snapshot': <String, Object?>{},
          'dataset_manifest_snapshot': <String, Object?>{},
          'current_step': 3,
          'total_steps': 3,
          'created_at': 'now',
          'updated_at': 'now',
        }),
      ],
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: FinetuneCenterPage(
            controller: controller,
            onOpenAdapter: () {},
          ),
        ),
      ),
    );

    expect(find.text('Fine-tune Center'), findsOneWidget);
    expect(find.text('adapter'), findsOneWidget);
    expect(find.byKey(const Key('finetune-new-run')), findsOneWidget);
    expect(find.textContaining('Adapter Evaluation'), findsNothing);
    expect(find.text('Evaluate Adapter'), findsNothing);
  });

  testWidgets('finetune_center capability flag controls navigation entry', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(900, 1200));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: buildShellNavigation(
            selectedIndex: 0,
            onSelected: (_) {},
            showNovelStudio: true,
            showFinetuneCenter: false,
          ),
        ),
      ),
    );
    expect(find.text('Fine-tune'), findsNothing);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: buildShellNavigation(
            selectedIndex: 0,
            onSelected: (_) {},
            showNovelStudio: true,
            showFinetuneCenter: true,
          ),
        ),
      ),
    );
    expect(find.text('Fine-tune'), findsOneWidget);
  });
}
