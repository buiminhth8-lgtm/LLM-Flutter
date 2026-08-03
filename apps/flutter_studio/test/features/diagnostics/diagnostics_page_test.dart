import 'package:flutter/material.dart';
import 'package:flutter_studio/features/diagnostics/diagnostics_page.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Diagnostics page shows health and export action', (
    tester,
  ) async {
    var refreshed = false;
    var exported = false;
    await tester.binding.setSurfaceSize(const Size(1200, 900));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(
      MaterialApp(
        home: DiagnosticsPage(
          runtime: const {'device': 'cpu'},
          capabilities: const [
            {'name': 'health_checks', 'status': 'available'},
          ],
          exportResult: null,
          health: const {'status': 'ok'},
          system: const {'platform': 'Windows'},
          preview: const {'capabilities_count': 1},
          onRefresh: () => refreshed = true,
          onExport: () => exported = true,
        ),
      ),
    );

    expect(find.text('诊断'), findsOneWidget);
    expect(find.text('已脱敏'), findsOneWidget);
    expect(find.textContaining('不包含模型权重'), findsOneWidget);
    await tester.tap(find.text('刷新检查'));
    await tester.tap(find.text('导出诊断'));
    expect(refreshed, isTrue);
    expect(exported, isTrue);
  });
}
