import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_studio/core/models/dto.dart';
import 'package:flutter_studio/features/adapters/adapters_page.dart';
import 'package:flutter_studio/features/benchmarks/benchmarks_page.dart';
import 'package:flutter_studio/features/diagnostics/diagnostics_page.dart';
import 'package:flutter_studio/features/downloads/downloads_page.dart';
import 'package:flutter_studio/features/models/models_page.dart';
import 'package:flutter_studio/features/rag/rag_page.dart';
import 'package:flutter_studio/features/storage/storage_page.dart';

Widget _wrap(Widget child) => MaterialApp(home: Scaffold(body: child));

void main() {
  testWidgets('Downloads totalBytes=null shows indeterminate progress and cancel request text', (tester) async {
    await tester.pumpWidget(
      _wrap(
        DownloadsPage(
          downloads: [
            DownloadTaskDto.fromMap({
              'job_id': 'job-1',
              'repo_id': 'org/model',
              'status': 'running',
              'downloaded_bytes': 1024,
              'total_bytes': null,
              'percent': null,
              'cancel_requested': true,
              'can_cancel': true,
            }),
          ],
          repoController: TextEditingController(),
          revisionController: TextEditingController(),
          allowPatternsController: TextEditingController(),
          ignorePatternsController: TextEditingController(),
          onStart: () {},
          onCancel: (_) async {},
          onRetry: (_) async {},
          onViewModel: (_) async {},
          onRefresh: () {},
        ),
      ),
    );

    expect(find.text('1.0 KB / 总大小未知'), findsOneWidget);
    expect(find.text('取消请求已提交'), findsOneWidget);
    expect(find.text('进度未知'), findsOneWidget);
  });

  testWidgets('Models move to trash uses confirmation dialog', (tester) async {
    var deleted = false;
    await tester.pumpWidget(
      _wrap(
        ModelsPage(
          models: const [
            {'id': 'model-a', 'status': 'ready', 'format': 'gguf', 'display_name': 'Model A'},
          ],
          currentModel: const {'loaded': false},
          selectedModelId: null,
          onRefresh: () {},
          onScan: () {},
          onLoad: (_) async {},
          onUnload: () {},
          onSelect: (_) async {},
          onRegisterExternal: () {},
          onMoveToTrash: (_) async => deleted = true,
        ),
      ),
    );

    await tester.ensureVisible(find.text('移入回收站'));
    await tester.tap(find.text('移入回收站'));
    await tester.pumpAndSettle();
    expect(find.text('移入回收站？'), findsOneWidget);
    await tester.tap(find.widgetWithText(FilledButton, '移入回收站').last);
    await tester.pumpAndSettle();
    expect(deleted, isTrue);
  });

  testWidgets('Adapter load and activate are disabled without model context', (tester) async {
    await tester.pumpWidget(
      _wrap(
        AdaptersPage(
          adapters: const [
            {'id': 'adapter-a', 'name': 'Adapter A', 'compatible': true},
          ],
          currentModel: null,
          hasModelContext: false,
          onRefresh: () {},
          onScan: () {},
          onLoad: (_) async {},
          onActivate: (_) async {},
          onDeactivate: (_) async {},
        ),
      ),
    );

    final load = tester.widget<FilledButton>(find.widgetWithText(FilledButton, 'Load'));
    final activate = tester.widget<FilledButton>(find.widgetWithText(FilledButton, 'Activate'));
    expect(load.onPressed, isNull);
    expect(activate.onPressed, isNull);
  });

  testWidgets('Benchmark page shows experimental notice', (tester) async {
    await tester.pumpWidget(
      _wrap(BenchmarksPage(benchmarks: const [], currentModel: const {}, onStart: () {}, onRefresh: () {})),
    );

    expect(find.text('Experimental'), findsOneWidget);
    expect(find.textContaining('仅供本机开发参考'), findsOneWidget);
  });

  testWidgets('Storage cleanup requires preview first', (tester) async {
    await tester.pumpWidget(
      _wrap(StoragePage(storage: const {'categories': []}, cleanupPreview: null, onRefresh: () {}, onPreview: () {}, onCleanup: () {})),
    );

    final cleanup = tester.widget<FilledButton>(find.widgetWithText(FilledButton, 'Execute cleanup'));
    expect(cleanup.onPressed, isNull);
    expect(find.text('未生成清理预览'), findsOneWidget);
  });

  testWidgets('Diagnostics page shows redaction policy', (tester) async {
    await tester.pumpWidget(
      _wrap(DiagnosticsPage(runtime: const {}, capabilities: const [], exportResult: null, onExport: () {})),
    );

    expect(find.text('Redacted'), findsOneWidget);
    expect(find.textContaining('不会包含模型权重'), findsOneWidget);
  });

  testWidgets('RAG page mentions local path restriction', (tester) async {
    await tester.pumpWidget(
      _wrap(RagPage(queryController: TextEditingController(), result: null, onQuery: () {})),
    );

    expect(find.text('Local paths restricted'), findsOneWidget);
    expect(find.textContaining('question'), findsWidgets);
  });
}
