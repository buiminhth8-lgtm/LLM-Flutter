import 'package:flutter/material.dart';

class AppStatusBadge extends StatelessWidget {
  const AppStatusBadge({
    super.key,
    required this.label,
    this.tone = AppStatusTone.neutral,
  });

  final String label;
  final AppStatusTone tone;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final (background, foreground) = switch (tone) {
      AppStatusTone.success => (Colors.green.shade50, Colors.green.shade800),
      AppStatusTone.warning => (Colors.amber.shade50, Colors.amber.shade900),
      AppStatusTone.danger => (scheme.errorContainer, scheme.onErrorContainer),
      AppStatusTone.info => (
        scheme.primaryContainer,
        scheme.onPrimaryContainer,
      ),
      AppStatusTone.neutral => (
        scheme.surfaceContainerHighest,
        scheme.onSurfaceVariant,
      ),
    };
    return DecoratedBox(
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        child: Text(
          label,
          style: TextStyle(color: foreground, fontWeight: FontWeight.w600),
        ),
      ),
    );
  }
}

enum AppStatusTone { neutral, info, success, warning, danger }
