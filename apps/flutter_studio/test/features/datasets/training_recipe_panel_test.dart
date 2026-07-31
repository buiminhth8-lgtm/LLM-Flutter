import 'package:flutter/material.dart';
import 'package:flutter_studio/features/datasets/models/recipe_recommend_request_dto.dart';
import 'package:flutter_studio/features/datasets/models/training_recipe_dto.dart';
import 'package:flutter_studio/features/datasets/widgets/training_recipe_panel.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets(
    'Training Recipe Panel requests recommendation and confirms recipe',
    (tester) async {
      RecipeRecommendRequestDto? request;
      var confirmed = false;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: TrainingRecipePanel(
                recipe: const TrainingRecipeDto(
                  recipeId: 'recipe-1',
                  datasetVersionId: 'dsv-1',
                  method: 'qlora',
                  recommendedConfig: {'epochs': 3, 'learning_rate': 0.0002},
                  userConfig: {},
                  status: 'draft',
                  createdAt: 'now',
                  updatedAt: 'now',
                  estimatedVramGb: 7.5,
                  estimatedTrainTimeMinutes: 12,
                ),
                onRecommend: (value) => request = value,
                onSaveConfig: (_) {},
                onConfirm: () => confirmed = true,
              ),
            ),
          ),
        ),
      );

      await tester.tap(find.byKey(const Key('recipe-recommend')));
      await tester.pump();
      await tester.tap(find.byKey(const Key('recipe-confirm')));
      await tester.pump();

      expect(request?.method, 'qlora');
      expect(confirmed, isTrue);
      expect(find.textContaining('does not start training'), findsOneWidget);
      expect(find.text('Start Training'), findsNothing);
    },
  );
}
