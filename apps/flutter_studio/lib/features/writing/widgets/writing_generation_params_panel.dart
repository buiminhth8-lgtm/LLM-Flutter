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
          Expanded(child: _field('Temperature', temperature)),
          const SizedBox(width: 8),
          Expanded(child: _field('Top P', topP)),
        ],
      ),
      const SizedBox(height: 8),
      Row(
        children: [
          Expanded(child: _field('Max tokens', maxTokens, integer: true)),
          const SizedBox(width: 8),
          Expanded(child: _field('Repeat penalty', repetitionPenalty)),
        ],
      ),
    ],
  );

  Widget _field(
    String label,
    TextEditingController controller, {
    bool integer = false,
  }) => TextField(
    key: Key('writing-${label.toLowerCase().replaceAll(' ', '-')}'),
    controller: controller,
    keyboardType: TextInputType.numberWithOptions(decimal: !integer),
    decoration: InputDecoration(
      labelText: label,
      border: const OutlineInputBorder(),
      isDense: true,
    ),
  );
}
