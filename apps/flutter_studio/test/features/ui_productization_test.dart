import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_studio/core/models/dto.dart';
import 'package:flutter_studio/features/adapters/adapters_page.dart';
import 'package:flutter_studio/features/benchmarks/benchmarks_page.dart';
import 'package:flutter_studio/features/diagnostics/diagnostics_page.dart';
import 'package:flutter_studio/features/downloads/downloads_page.dart';
import 'package:flutter_studio/features/models/models_page.dart';
import 'package:flutter_studio/features/novel_studio/novel_studio_placeholder_page.dart';
import 'package:flutter_studio/features/rag/rag_page.dart';
import 'package:flutter_studio/features/storage/storage_page.dart';

Widget _wrap(Widget child) => MaterialApp(home: Scaffold(body: child));

void main() {
  testWidgets('Downloads shows ModelScope and unknown total progress state', (
    tester,
  ) async {
    String selectedProvider = 'modelscope';

    await tester.pumpWidget(
      _wrap(
        DownloadsPage(
          downloads: [
            DownloadTaskDto.fromMap({
              'job_id': 'job-1',
              'provider': 'modelscope',
              'repo_id': 'org/model',
              'status': 'running',
              'downloaded_bytes': 1024,
              'total_bytes': null,
              'percent': null,
              'cancel_requested': true,
              'can_cancel': true,
              'can_delete': false,
            }),
            DownloadTaskDto.fromMap({
              'job_id': 'job-2',
              'provider': 'modelscope',
              'repo_id': 'org/done',
              'status': 'succeeded',
              'downloaded_bytes': 1024,
              'total_bytes': 1024,
              'percent': 100.0,
              'can_delete': true,
            }),
          ],
          repoController: TextEditingController(),
          provider: selectedProvider,
          revisionController: TextEditingController(),
          allowPatternsController: TextEditingController(),
          ignorePatternsController: TextEditingController(),
          onStart: () {},
          onProviderChanged: (value) => selectedProvider = value,
          onCancel: (_) async {},
          onRetry: (_) async {},
          onDelete: (_) async {},
          onViewModel: (_) async {},
          onRefresh: () {},
        ),
      ),
    );

    expect(find.text('ModelScope / 魔塔社区'), findsWidgets);
    expect(find.text('ModelScope / 魔塔社区: org/model'), findsOneWidget);
    expect(find.text('Hugging Face'), findsNothing);
    expect(find.text('1.0 KB / 总大小未知'), findsOneWidget);
    expect(find.text('取消请求已提交'), findsOneWidget);
    expect(find.text('进度未知'), findsOneWidget);
    expect(find.text('删除记录'), findsNWidgets(2));
  });

  testWidgets('Downloads can delete terminal records and copy errors', (
    tester,
  ) async {
    var deletedJobId = '';

    await tester.pumpWidget(
      _wrap(
        DownloadsPage(
          downloads: [
            DownloadTaskDto.fromMap({
              'job_id': 'job-failed',
              'provider': 'modelscope',
              'repo_id': 'org/failed',
              'status': 'failed',
              'downloaded_bytes': 0,
              'total_bytes': null,
              'error_code': 'DOWNLOAD_NETWORK_ERROR',
              'error_message': 'network failed',
            }),
          ],
          repoController: TextEditingController(),
          provider: 'modelscope',
          revisionController: TextEditingController(),
          allowPatternsController: TextEditingController(),
          ignorePatternsController: TextEditingController(),
          onStart: () {},
          onProviderChanged: (_) {},
          onCancel: (_) async {},
          onRetry: (_) async {},
          onDelete: (id) async => deletedJobId = id,
          onViewModel: (_) async {},
          onRefresh: () {},
        ),
      ),
    );

    expect(find.text('下载失败'), findsOneWidget);
    expect(find.textContaining('DOWNLOAD_NETWORK_ERROR'), findsOneWidget);
    expect(find.byIcon(Icons.copy), findsOneWidget);

    await tester.tap(find.text('删除记录'));
    await tester.pumpAndSettle();
    expect(find.text('删除下载记录？'), findsOneWidget);
    await tester.tap(find.widgetWithText(FilledButton, '删除记录').last);
    await tester.pumpAndSettle();
    expect(deletedJobId, 'job-failed');
  });

  testWidgets('Models move to trash uses confirmation dialog', (tester) async {
    var deleted = false;
    await tester.pumpWidget(
      _wrap(
        ModelsPage(
          models: const [
            {
              'id': 'model-a',
              'status': 'ready',
              'format': 'gguf',
              'display_name': 'Model A',
            },
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

  testWidgets('Adapter load and activate are disabled without model context', (
    tester,
  ) async {
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

    final load = tester.widget<FilledButton>(
      find.widgetWithText(FilledButton, 'Load'),
    );
    final activate = tester.widget<FilledButton>(
      find.widgetWithText(FilledButton, 'Activate'),
    );
    expect(load.onPressed, isNull);
    expect(activate.onPressed, isNull);
  });

  testWidgets('Benchmark page shows experimental notice', (tester) async {
    await tester.pumpWidget(
      _wrap(
        BenchmarksPage(
          benchmarks: const [],
          currentModel: const {},
          onStart: () {},
          onRefresh: () {},
        ),
      ),
    );

    expect(find.text('Experimental'), findsOneWidget);
    expect(find.textContaining('仅供本机开发参考'), findsOneWidget);
  });

  testWidgets('Storage cleanup requires preview first', (tester) async {
    await tester.pumpWidget(
      _wrap(
        StoragePage(
          storage: const {'categories': []},
          cleanupPreview: null,
          onRefresh: () {},
          onPreview: () {},
          onCleanup: () {},
        ),
      ),
    );

    final cleanup = tester.widget<FilledButton>(
      find.widgetWithText(FilledButton, 'Execute cleanup'),
    );
    expect(cleanup.onPressed, isNull);
    expect(find.text('未生成清理预览'), findsOneWidget);
  });

  testWidgets('Diagnostics page shows redaction policy', (tester) async {
    await tester.pumpWidget(
      _wrap(
        DiagnosticsPage(
          runtime: const {},
          capabilities: const [],
          exportResult: null,
          onExport: () {},
        ),
      ),
    );

    expect(find.text('Redacted'), findsOneWidget);
    expect(find.textContaining('不会包含模型权重'), findsOneWidget);
  });

  testWidgets('RAG page mentions local path restriction', (tester) async {
    await tester.pumpWidget(
      _wrap(
        RagPage(
          queryController: TextEditingController(),
          result: null,
          onQuery: () {},
        ),
      ),
    );

    expect(find.text('Local paths restricted'), findsOneWidget);
    expect(find.textContaining('question'), findsWidgets);
  });

  testWidgets('Novel Studio placeholder is roadmap only', (tester) async {
    await tester.pumpWidget(_wrap(const NovelStudioPlaceholderPage()));

    expect(find.text('Novel Studio is planned.'), findsOneWidget);
    expect(find.text('阶段 0：工程基线准备中。'), findsOneWidget);
    expect(find.text('下一阶段：Novel 项目与基础资料库。'), findsOneWidget);
  });
}
