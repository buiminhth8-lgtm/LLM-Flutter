import 'package:flutter/material.dart';
import 'package:flutter_studio/features/novel_studio/novel_studio_dashboard_page.dart';
import 'package:flutter_test/flutter_test.dart';

List<Map<String, Object?>> _caps() => [
  for (final name in [
    'novel_studio',
    'novel_projects',
    'prompt_studio',
    'context_assembler',
    'writing_workspace',
    'revision_system',
    'dataset_builder',
    'dataset_versioning',
    'finetune_center',
    'adapter_evaluation',
    'novel_rag_memory',
    'full_evaluation_center',
    'novel_studio_product_ui',
  ])
    {
      'name': name,
      'status': name == 'novel_studio' ? 'partial' : 'available',
      'frontend_exposed': true,
    },
];

void main() {
  testWidgets('Novel Studio Dashboard shows workflow and quick actions', (
    tester,
  ) async {
    var openedWriting = false;
    await tester.binding.setSurfaceSize(const Size(1400, 1000));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(
      MaterialApp(
        home: NovelStudioDashboardPage(
          capabilities: _caps(),
          projectCount: 2,
          chapterCount: 5,
          generationCount: 3,
          revisionCount: 1,
          datasetCount: 1,
          finetuneRunCount: 0,
          evaluationRunCount: 2,
          backendStatus: 'healthy',
          modelLabel: 'qwen-local',
          adapterLabel: '无',
          runningJobs: 0,
          health: const {'status': 'ok'},
          onRefresh: () {},
          onOpenProjects: () {},
          onOpenPrompts: () {},
          onOpenContext: () {},
          onOpenWriting: () => openedWriting = true,
          onOpenRevisions: () {},
          onOpenDataset: () {},
          onOpenFinetune: () {},
          onOpenAdapterEvaluation: () {},
          onOpenMemory: () {},
          onOpenEvaluation: () {},
          onOpenDiagnostics: () {},
        ),
      ),
    );

    expect(find.text('小说工作台仪表盘'), findsOneWidget);
    expect(find.text('工作流地图'), findsOneWidget);
    expect(find.text('项目'), findsWidgets);
    expect(find.text('写作'), findsWidgets);
    expect(find.text('最近活动'), findsOneWidget);

    await tester.tap(find.widgetWithText(FilledButton, '写作'));
    expect(openedWriting, isTrue);
  });
}
