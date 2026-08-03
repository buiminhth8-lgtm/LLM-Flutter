import 'package:flutter/material.dart';
import 'package:flutter_studio/features/finetune/models/finetune_preflight_dto.dart';
import 'package:flutter_studio/features/finetune/widgets/finetune_preflight_panel.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Preflight panel displays errors and warnings', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: FinetunePreflightPanel(
            result: FinetunePreflightDto(
              ok: false,
              errors: [
                {'code': 'FINETUNE_DEPENDENCY_MISSING', 'message': 'missing'},
              ],
              warnings: [
                {'code': 'FINETUNE_NO_VALIDATION_SPLIT', 'message': 'no val'},
              ],
              resolvedConfig: {'method': 'qlora'},
            ),
          ),
        ),
      ),
    );

    expect(find.text('ok=false'), findsOneWidget);
    expect(find.textContaining('FINETUNE_DEPENDENCY_MISSING'), findsOneWidget);
    expect(find.textContaining('FINETUNE_NO_VALIDATION_SPLIT'), findsOneWidget);
    expect(find.textContaining('qlora'), findsOneWidget);
  });
}
