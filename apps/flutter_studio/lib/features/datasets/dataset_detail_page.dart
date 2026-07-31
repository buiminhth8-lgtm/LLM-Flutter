import 'package:flutter/material.dart';

import 'dataset_builder_page.dart';
import 'dataset_controller.dart';

class DatasetDetailPage extends StatelessWidget {
  const DatasetDetailPage({super.key, required this.controller});

  final DatasetController controller;

  @override
  Widget build(BuildContext context) =>
      DatasetBuilderPage(controller: controller);
}
