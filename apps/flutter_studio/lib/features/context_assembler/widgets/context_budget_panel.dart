import 'package:flutter/material.dart';

import '../models/context_budget_dto.dart';

class ContextBudgetPanel extends StatelessWidget {
  const ContextBudgetPanel({
    super.key,
    required this.maxTokens,
    required this.reservedOutputTokens,
    required this.maxContextTokens,
    required this.maxChars,
    this.result,
  });

  final TextEditingController maxTokens;
  final TextEditingController reservedOutputTokens;
  final TextEditingController maxContextTokens;
  final TextEditingController maxChars;
  final ContextBudgetDto? result;

  ContextBudgetDto value() => ContextBudgetDto(
    maxTokens: int.tryParse(maxTokens.text) ?? 4096,
    reservedOutputTokens: int.tryParse(reservedOutputTokens.text) ?? 1200,
    maxContextTokens: int.tryParse(maxContextTokens.text) ?? 2500,
    maxChars: int.tryParse(maxChars.text) ?? 12000,
  );

  @override
  Widget build(BuildContext context) {
    final estimatedTokens = result?.estimatedTokens ?? 0;
    final maxContext = result?.maxContextTokens ?? value().maxContextTokens;
    final ratio = maxContext <= 0 ? 0.0 : estimatedTokens / maxContext;
    final color = ratio > 1
        ? Theme.of(context).colorScheme.error
        : ratio >= .8
        ? Colors.amber.shade800
        : Theme.of(context).colorScheme.primary;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('上下文预算', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(child: _numberField(maxTokens, 'max_tokens')),
            const SizedBox(width: 8),
            Expanded(
              child: _numberField(
                reservedOutputTokens,
                'reserved_output_tokens',
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: _numberField(maxContextTokens, 'max_context_tokens'),
            ),
            const SizedBox(width: 8),
            Expanded(child: _numberField(maxChars, 'max_chars')),
          ],
        ),
        if (result != null) ...[
          const SizedBox(height: 12),
          LinearProgressIndicator(
            value: ratio.clamp(0, 1),
            color: color,
            minHeight: 8,
          ),
          const SizedBox(height: 6),
          Text(
        '估算 $estimatedTokens Token / ${result!.estimatedChars ?? 0} 字符',
            style: TextStyle(color: color),
          ),
        ],
      ],
    );
  }

  Widget _numberField(TextEditingController controller, String label) =>
      TextField(
        controller: controller,
        keyboardType: TextInputType.number,
        decoration: InputDecoration(
          labelText: label,
          border: const OutlineInputBorder(),
          isDense: true,
        ),
      );
}
