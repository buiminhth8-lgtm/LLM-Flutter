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
      content: Text(
        message ??
            '$featureName is not enabled by backend capabilities. Open Settings to verify the backend and feature flags.',
      ),
      actions: [
        if (onOpenSettings != null)
          TextButton(
            onPressed: onOpenSettings,
            child: const Text('Open Settings'),
          ),
      ],
    );
  }
}
