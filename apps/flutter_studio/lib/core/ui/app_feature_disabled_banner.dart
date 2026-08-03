import 'package:flutter/material.dart';

class AppFeatureDisabledBanner extends StatelessWidget {
  const AppFeatureDisabledBanner({
    super.key,
    required this.featureName,
    this.message,
    this.onOpenSettings,
  });

  final String featureName;
  final String? message;
  final VoidCallback? onOpenSettings;

  @override
  Widget build(BuildContext context) {
    return MaterialBanner(
      leading: const Icon(Icons.info_outline),
      content: Text(message ?? '$featureName 未在后端能力中启用。请打开设置检查后端与功能开关。'),
      actions: [
        if (onOpenSettings != null)
          TextButton(onPressed: onOpenSettings, child: const Text('打开设置')),
      ],
    );
  }
}
