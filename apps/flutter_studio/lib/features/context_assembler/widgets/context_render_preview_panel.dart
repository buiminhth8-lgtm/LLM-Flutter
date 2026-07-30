import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../models/context_render_preview_dto.dart';

class ContextRenderPreviewPanel extends StatelessWidget {
  const ContextRenderPreviewPanel({super.key, required this.preview});

  final ContextRenderPreviewDto preview;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                'Prompt 渲染预览',
                style: Theme.of(context).textTheme.titleMedium,
              ),
            ),
            IconButton(
              onPressed: () => Clipboard.setData(
                ClipboardData(text: preview.renderedPrompt),
              ),
              icon: const Icon(Icons.copy_outlined),
              tooltip: 'Copy rendered prompt',
            ),
          ],
        ),
        SelectableText(preview.renderedPrompt),
        const SizedBox(height: 8),
        Text('prompt_hash: ${preview.promptHash}'),
        if (preview.missingVariables.isNotEmpty)
          Text('缺失变量：${preview.missingVariables.join(', ')}'),
        if (preview.renderWarnings.isNotEmpty)
          Text('渲染警告：${preview.renderWarnings.join(', ')}'),
      ],
    );
  }
}
