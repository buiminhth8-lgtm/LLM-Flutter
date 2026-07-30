import 'package:flutter/material.dart';
import 'package:flutter_studio/features/context_assembler/models/context_budget_dto.dart';
import 'package:flutter_studio/features/context_assembler/widgets/context_budget_panel.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Budget panel displays token and character estimates', (
    tester,
  ) async {
    final controllers = List.generate(
      4,
      (index) =>
          TextEditingController(text: ['4096', '1200', '2500', '12000'][index]),
    );
    addTearDown(() {
      for (final controller in controllers) {
        controller.dispose();
      }
    });

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ContextBudgetPanel(
            maxTokens: controllers[0],
            reservedOutputTokens: controllers[1],
            maxContextTokens: controllers[2],
            maxChars: controllers[3],
            result: const ContextBudgetDto(
              estimatedTokens: 1980,
              estimatedChars: 5320,
            ),
          ),
        ),
      ),
    );

    expect(find.textContaining('1980 tokens'), findsOneWidget);
    expect(find.textContaining('5320 字符'), findsOneWidget);
    expect(find.byType(LinearProgressIndicator), findsOneWidget);
  });
}
