import 'package:flutter/material.dart';

import '../../core/ui/app_section_header.dart';
import 'dataset_controller.dart';
import 'widgets/training_recipe_panel.dart';

class TrainingRecipePreviewPage extends StatelessWidget {
  const TrainingRecipePreviewPage({super.key, required this.controller});

  final DatasetController controller;

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
    animation: controller,
    builder: (context, _) => Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const AppSectionHeader(
            title: 'Training Recipe Preview',
            subtitle:
                'Recommend and confirm a draft recipe only; no training is started.',
          ),
          Expanded(
            child: SingleChildScrollView(
              child: TrainingRecipePanel(
                recipe: controller.state.currentRecipe,
                onRecommend: controller.recommendRecipe,
                onSaveConfig: controller.updateCurrentRecipe,
                onConfirm: controller.confirmCurrentRecipe,
              ),
            ),
          ),
        ],
      ),
    ),
  );
}
