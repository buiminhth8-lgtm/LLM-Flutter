import 'package:flutter/material.dart';

class DiagnosticsPage extends StatelessWidget {
  const DiagnosticsPage({
    super.key,
    required this.runtime,
    required this.capabilities,
    required this.exportResult,
    required this.onExport,
  });

  final Map<String, dynamic>? runtime;
  final List<dynamic> capabilities;
  final String? exportResult;
  final VoidCallback onExport;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('Diagnostics', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
        const SizedBox(height: 8),
        const Text('Diagnostic packages include redacted runtime, dependency, task, model metadata, disk and capability summaries. They do not include model weights, chat text, RAG document text, passwords, API keys, cookies or authorization headers.'),
        const SizedBox(height: 12),
        FilledButton.icon(onPressed: onExport, icon: const Icon(Icons.archive_outlined), label: const Text('Export diagnostics package')),
        if (exportResult != null) ...[
          const SizedBox(height: 12),
          SelectableText(exportResult!),
        ],
        const SizedBox(height: 12),
        Expanded(
          child: Row(children: [
            Expanded(child: Card(child: SingleChildScrollView(padding: const EdgeInsets.all(12), child: SelectableText('Runtime\n${runtime ?? {}}')))),
            const SizedBox(width: 12),
            Expanded(child: Card(child: ListView(padding: const EdgeInsets.all(12), children: capabilities.map((item) => Text('$item')).toList()))),
          ]),
        ),
      ]),
    );
  }
}
