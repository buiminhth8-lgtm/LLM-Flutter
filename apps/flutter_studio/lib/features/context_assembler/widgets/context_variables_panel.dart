import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class ContextVariablesPanel extends StatelessWidget {
  const ContextVariablesPanel({super.key, required this.variables});

  final Map<String, dynamic> variables;

  @override
  Widget build(BuildContext context) {
    final json = const JsonEncoder.withIndent('  ').convert(variables);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                '装配变量',
                style: Theme.of(context).textTheme.titleMedium,
              ),
            ),
            IconButton(
              onPressed: () => Clipboard.setData(ClipboardData(text: json)),
              icon: const Icon(Icons.copy_outlined),
              tooltip: 'Copy variables JSON',
            ),
          ],
        ),
        SelectableText(json),
      ],
    );
  }
}
