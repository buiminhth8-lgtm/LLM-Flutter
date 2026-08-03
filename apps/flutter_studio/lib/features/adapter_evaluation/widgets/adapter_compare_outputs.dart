import 'package:flutter/material.dart';

import '../models/adapter_eval_result_dto.dart';

class AdapterCompareOutputs extends StatelessWidget {
  const AdapterCompareOutputs({super.key, required this.results});

  final List<AdapterEvalResultDto> results;

  @override
  Widget build(BuildContext context) {
    final base = _variant('base');
    final adapter = _variant('adapter');
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(child: _panel(context, '基础模型输出', base)),
        const SizedBox(width: 12),
        Expanded(child: _panel(context, '适配器输出', adapter)),
      ],
    );
  }

  AdapterEvalResultDto? _variant(String variant) {
    for (final item in results) {
      if (item.variant == variant) {
        return item;
      }
    }
    return null;
  }

  Widget _panel(
    BuildContext context,
    String title,
    AdapterEvalResultDto? result,
  ) {
    final text = result == null
        ? '尚未生成。'
        : result.status == 'failed'
        ? '失败：${result.errorCode ?? ''} ${result.errorMessage ?? ''}'
        : result.outputText;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleMedium),
            Text('状态：${result?.status ?? '-'}'),
            const Divider(),
            SizedBox(
              height: 300,
              child: SingleChildScrollView(child: SelectableText(text)),
            ),
          ],
        ),
      ),
    );
  }
}
