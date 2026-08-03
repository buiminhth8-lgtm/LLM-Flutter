import 'package:flutter/material.dart';
import 'package:flutter_studio/features/writing/widgets/writing_generation_params_panel.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('generation params panel exposes Stage 4 controls', (
    tester,
  ) async {
    final temperature = TextEditingController(text: '0.8');
    final topP = TextEditingController(text: '0.9');
    final maxTokens = TextEditingController(text: '2048');
    final repetitionPenalty = TextEditingController(text: '1.1');
    addTearDown(temperature.dispose);
    addTearDown(topP.dispose);
    addTearDown(maxTokens.dispose);
    addTearDown(repetitionPenalty.dispose);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: WritingGenerationParamsPanel(
            temperature: temperature,
            topP: topP,
            maxTokens: maxTokens,
            repetitionPenalty: repetitionPenalty,
          ),
        ),
      ),
    );

    expect(find.text('温度'), findsOneWidget);
    expect(find.text('Top P'), findsOneWidget);
    expect(find.text('最大 Token 数'), findsOneWidget);
    await tester.enterText(find.byKey(const Key('writing-max-tokens')), '4096');
    expect(maxTokens.text, '4096');
  });
}
