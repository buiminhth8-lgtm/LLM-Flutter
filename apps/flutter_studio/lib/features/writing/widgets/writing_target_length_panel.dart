import 'package:flutter/material.dart';

import '../models/target_length_dto.dart';

class WritingTargetLengthPanel extends StatelessWidget {
  const WritingTargetLengthPanel({
    super.key,
    required this.minimum,
    required this.maximum,
    required this.unit,
    required this.strategy,
    required this.onUnitChanged,
    required this.onStrategyChanged,
  });

  final TextEditingController minimum;
  final TextEditingController maximum;
  final String unit;
  final String strategy;
  final ValueChanged<String> onUnitChanged;
  final ValueChanged<String> onStrategyChanged;

  TargetLengthDto value() => TargetLengthDto(
    unit: unit,
    min: int.tryParse(minimum.text) ?? 1200,
    max: int.tryParse(maximum.text) ?? 1800,
    strategy: strategy,
  );

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text('目标长度', style: Theme.of(context).textTheme.titleSmall),
      const SizedBox(height: 8),
      Row(
        children: [
          Expanded(
            child: TextField(
              key: const Key('writing-target-min'),
              controller: minimum,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: '最少',
                border: OutlineInputBorder(),
                isDense: true,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: TextField(
              key: const Key('writing-target-max'),
              controller: maximum,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: '最多',
                border: OutlineInputBorder(),
                isDense: true,
              ),
            ),
          ),
        ],
      ),
      const SizedBox(height: 8),
      Row(
        children: [
          Expanded(
            child: DropdownButtonFormField<String>(
              initialValue: unit,
              items: const [
                DropdownMenuItem(value: 'chars', child: Text('中文字符')),
                DropdownMenuItem(value: 'tokens', child: Text('Tokens')),
              ],
              onChanged: (value) {
                if (value != null) onUnitChanged(value);
              },
              decoration: const InputDecoration(
                labelText: '单位',
                border: OutlineInputBorder(),
                isDense: true,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: DropdownButtonFormField<String>(
              initialValue: strategy,
              items: const [
                DropdownMenuItem(value: 'soft', child: Text('Soft')),
                DropdownMenuItem(value: 'hard', child: Text('Hard')),
              ],
              onChanged: (value) {
                if (value != null) onStrategyChanged(value);
              },
              decoration: const InputDecoration(
                labelText: '策略',
                border: OutlineInputBorder(),
                isDense: true,
              ),
            ),
          ),
        ],
      ),
    ],
  );
}
