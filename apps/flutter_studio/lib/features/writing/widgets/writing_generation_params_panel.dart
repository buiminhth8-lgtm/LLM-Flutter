import 'package:flutter/material.dart';

class WritingGenerationParamsPanel extends StatelessWidget {
  const WritingGenerationParamsPanel({
    super.key,
    required this.temperature,
    required this.topP,
    required this.maxTokens,
    required this.repetitionPenalty,
  });

  final TextEditingController temperature;
  final TextEditingController topP;
  final TextEditingController maxTokens;
  final TextEditingController repetitionPenalty;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text('生成参数', style: Theme.of(context).textTheme.titleSmall),
      const SizedBox(height: 8),
      Row(
        children: [
          Expanded(child: _field('温度', temperature, fieldKey: 'temperature')),
          const SizedBox(width: 8),
          Expanded(child: _field('Top P', topP, fieldKey: 'top-p')),
        ],
      ),
      const SizedBox(height: 8),
      Row(
        children: [
          Expanded(
            child: _field(
              '最大 Token 数',
              maxTokens,
              fieldKey: 'max-tokens',
              integer: true,
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: _field(
              '重复惩罚',
              repetitionPenalty,
              fieldKey: 'repetition-penalty',
            ),
          ),
        ],
      ),
    ],
  );

  Widget _field(
    String label,
    TextEditingController controller, {
    required String fieldKey,
    bool integer = false,
  }) => TextField(
    key: Key('writing-$fieldKey'),
    controller: controller,
    keyboardType: TextInputType.numberWithOptions(decimal: !integer),
    decoration: InputDecoration(
      labelText: label,
      border: const OutlineInputBorder(),
      isDense: true,
    ),
  );
}
