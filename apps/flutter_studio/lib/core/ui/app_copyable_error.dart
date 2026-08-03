import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class AppCopyableError extends StatelessWidget {
  const AppCopyableError({super.key, required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Theme.of(context).colorScheme.errorContainer,
      child: ListTile(
        leading: const Icon(Icons.error_outline),
        title: const Text('错误'),
        subtitle: SelectableText(message),
        trailing: IconButton(
          tooltip: '复制错误',
          icon: const Icon(Icons.copy),
          onPressed: () => Clipboard.setData(ClipboardData(text: message)),
        ),
      ),
    );
  }
}
