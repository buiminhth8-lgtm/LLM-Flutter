import 'package:flutter/material.dart';

import '../../context_assembler/models/context_render_preview_dto.dart';

class WritingContextPreviewPanel extends StatelessWidget {
  const WritingContextPreviewPanel({super.key, required this.preview});

  final ContextRenderPreviewDto? preview;

  @override
  Widget build(BuildContext context) {
    final value = preview;
    return ExpansionTile(
      key: const Key('writing-context-preview'),
      initiallyExpanded: value != null,
      title: const Text('上下文 / 提示词预览'),
      subtitle: Text(
        value == null
            ? '生成前可先装配并检查上下文'
            : 'Token ${value.assembly.estimatedTokens} · 字符 ${value.assembly.estimatedChars}',
      ),
      children: [
        if (value == null)
          const Padding(padding: EdgeInsets.all(12), child: Text('尚未渲染上下文预览。'))
        else
          ConstrainedBox(
            constraints: const BoxConstraints(maxHeight: 240),
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(12),
              child: SelectableText(value.renderedPrompt),
            ),
          ),
      ],
    );
  }
}
