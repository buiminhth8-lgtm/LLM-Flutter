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
            title: '训练配方预览',
            subtitle: '仅推荐并确认草稿配方，不启动训练。',
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
