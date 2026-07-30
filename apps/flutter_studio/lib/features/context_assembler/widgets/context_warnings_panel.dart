import 'package:flutter/material.dart';

import '../models/context_warning_dto.dart';

class ContextWarningsPanel extends StatelessWidget {
  const ContextWarningsPanel({super.key, required this.warnings});

  final List<ContextWarningDto> warnings;

  @override
  Widget build(BuildContext context) {
    if (warnings.isEmpty) {
      return const Text('未发生截断或预算警告。');
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('警告', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 6),
        for (final warning in warnings)
          ListTile(
            dense: true,
            contentPadding: EdgeInsets.zero,
            leading: Icon(
              warning.code == 'CONTEXT_BUDGET_EXCEEDED'
                  ? Icons.error_outline
                  : Icons.warning_amber_outlined,
              color: warning.code == 'CONTEXT_BUDGET_EXCEEDED'
                  ? Theme.of(context).colorScheme.error
                  : Colors.amber.shade800,
            ),
            title: Text(warning.code),
            subtitle: Text(
              '${warning.message}${warning.affected.isEmpty ? '' : '\n影响：${warning.affected.join(', ')}'}',
            ),
          ),
      ],
    );
  }
}
