import 'package:flutter/material.dart';
import 'package:flutter_studio/features/datasets/widgets/recipe_config_editor.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Recipe Config Editor edits user_config', (tester) async {
    Map<String, Object?>? saved;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: RecipeConfigEditor(
            initialConfig: const {'epochs': 3, 'learning_rate': 0.0002},
            onSave: (value) => saved = value,
          ),
        ),
      ),
    );

    await tester.enterText(find.byKey(const Key('recipe-epochs')), '2');
    await tester.tap(find.byKey(const Key('recipe-config-save')));
    await tester.pump();

    expect((saved?['user_config'] as Map?)?['epochs'], 2);
  });
}
