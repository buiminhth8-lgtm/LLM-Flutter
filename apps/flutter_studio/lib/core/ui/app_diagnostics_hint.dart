import 'package:flutter/material.dart';

class AppDiagnosticsHint extends StatelessWidget {
  const AppDiagnosticsHint({super.key, this.onOpenDiagnostics});

  final VoidCallback? onOpenDiagnostics;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: const Icon(Icons.bug_report_outlined),
        title: const Text('Need a support bundle?'),
        subtitle: const Text(
          'Diagnostics exports are redacted and exclude model weights, API keys, cookies, and document bodies.',
        ),
        trailing: onOpenDiagnostics == null
            ? null
            : OutlinedButton(
                onPressed: onOpenDiagnostics,
                child: const Text('Open Diagnostics'),
              ),
      ),
    );
  }
}
