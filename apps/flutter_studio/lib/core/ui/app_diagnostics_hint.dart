import 'package:flutter/material.dart';

class AppDiagnosticsHint extends StatelessWidget {
  const AppDiagnosticsHint({super.key, this.onOpenDiagnostics});

  final VoidCallback? onOpenDiagnostics;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: const Icon(Icons.bug_report_outlined),
        title: const Text('需要支持包？'),
        subtitle: const Text('诊断导出会脱敏，并排除模型权重、API Key、Cookie 和文档正文。'),
        trailing: onOpenDiagnostics == null
            ? null
            : OutlinedButton(
                onPressed: onOpenDiagnostics,
                child: const Text('打开诊断'),
              ),
      ),
    );
  }
}
