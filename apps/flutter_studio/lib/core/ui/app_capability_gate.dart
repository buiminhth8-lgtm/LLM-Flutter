import 'package:flutter/material.dart';

import 'app_empty_state.dart';

class AppCapabilityGate extends StatelessWidget {
  const AppCapabilityGate({
    super.key,
    required this.capabilityName,
    required this.capabilities,
    required this.child,
    this.fallback,
  });

  final String capabilityName;
  final List<dynamic> capabilities;
  final Widget child;
  final Widget? fallback;

  bool get available => capabilities.any((item) {
    if (item is! Map) {
      return false;
    }
    return item['name'] == capabilityName &&
        (item['status'] == 'available' || item['status'] == 'partial') &&
        item['frontend_exposed'] == true;
  });

  @override
  Widget build(BuildContext context) {
    if (available) {
      return child;
    }
    return fallback ??
        AppEmptyState(
          title: '能力不可用',
          message: '$capabilityName 已禁用或后端未暴露。',
          icon: Icons.lock_outline,
        );
  }
}
