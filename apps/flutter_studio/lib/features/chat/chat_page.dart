import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/models/dto.dart';
import '../../core/ui/app_empty_state.dart';
import '../../core/ui/app_section_header.dart';
import '../../core/ui/app_status_badge.dart';
import 'chat_controller.dart';

class ChatPage extends StatelessWidget {
  const ChatPage({
    super.key,
    required this.controller,
    required this.inputController,
    required this.systemController,
    required this.selectedModelId,
    required this.currentModel,
    required this.onSend,
    required this.onStop,
    required this.onClear,
    required this.onRegenerate,
    required this.onStreamingChanged,
  });

  final ChatController controller;
  final TextEditingController inputController;
  final TextEditingController systemController;
  final String? selectedModelId;
  final Map<String, dynamic>? currentModel;
  final VoidCallback onSend;
  final VoidCallback onStop;
  final VoidCallback onClear;
  final VoidCallback onRegenerate;
  final ValueChanged<bool> onStreamingChanged;

  @override
  Widget build(BuildContext context) {
    final loaded = currentModel?['loaded'] == true;
    final modelId = selectedModelId ?? (loaded ? '${currentModel?['model_id'] ?? ''}' : '');
    final adapter = '${currentModel?['adapter_id'] ?? currentModel?['adapter'] ?? ''}'.trim();
    final canChat = modelId.isNotEmpty && loaded && !controller.isGenerating;
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          AppSectionHeader(
            title: 'Chat',
            subtitle: loaded ? '当前模型：$modelId' : '请先在 Models 页面加载模型。',
            actions: [
              AppStatusBadge(
                label: loaded ? '已加载' : '未加载',
                tone: loaded ? AppStatusTone.success : AppStatusTone.warning,
              ),
              const SizedBox(width: 8),
              AppStatusBadge(label: adapter.isEmpty ? 'Adapter: None' : 'Adapter: $adapter'),
              const SizedBox(width: 12),
              const Text('Stream'),
              Switch(value: controller.streamingEnabled, onChanged: controller.isGenerating ? null : onStreamingChanged),
              IconButton.filledTonal(onPressed: onClear, icon: const Icon(Icons.delete_outline), tooltip: '清空历史'),
            ],
          ),
          const SizedBox(height: 12),
          TextField(
            controller: systemController,
            enabled: loaded,
            decoration: const InputDecoration(labelText: 'System Prompt', border: OutlineInputBorder()),
          ),
          const SizedBox(height: 12),
          Expanded(
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surface,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
              ),
              child: controller.turns.isEmpty
                  ? AppEmptyState(
                      title: loaded ? '开始对话' : '请先加载模型',
                      message: loaded ? '输入消息后按 Enter 发送，Shift + Enter 换行。' : '模型加载后才能发送聊天请求。',
                      icon: Icons.chat_bubble_outline,
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(12),
                      itemCount: controller.turns.length,
                      itemBuilder: (context, index) {
                        final ChatTurn turn = controller.turns[index];
                        return _ChatBubble(
                          turn: turn,
                          generating: index == controller.turns.length - 1 && controller.isGenerating,
                        );
                      },
                    ),
            ),
          ),
          if (controller.lastError != null) ...[
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerLeft,
              child: Text(controller.lastError!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ),
          ],
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: inputController,
                  enabled: canChat,
                  minLines: 1,
                  maxLines: 4,
                  decoration: InputDecoration(
                    hintText: loaded ? '输入消息' : '请先加载模型',
                    border: const OutlineInputBorder(),
                  ),
                  textInputAction: TextInputAction.send,
                  onSubmitted: (_) {
                    if (canChat) {
                      onSend();
                    }
                  },
                ),
              ),
              const SizedBox(width: 8),
              IconButton.filledTonal(
                onPressed: controller.turns.any((turn) => turn.role == 'user') && !controller.isGenerating ? onRegenerate : null,
                icon: const Icon(Icons.refresh),
                tooltip: '重新生成',
              ),
              const SizedBox(width: 8),
              if (controller.isGenerating)
                FilledButton.icon(onPressed: onStop, icon: const Icon(Icons.stop), label: const Text('停止'))
              else
                FilledButton.icon(onPressed: canChat ? onSend : null, icon: const Icon(Icons.send), label: const Text('发送')),
            ],
          ),
        ],
      ),
    );
  }
}

class _ChatBubble extends StatelessWidget {
  const _ChatBubble({required this.turn, required this.generating});

  final ChatTurn turn;
  final bool generating;

  @override
  Widget build(BuildContext context) {
    final isUser = turn.role == 'user';
    final content = turn.content.isEmpty && generating ? '生成中...' : turn.content;
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 780),
        child: Card(
          color: isUser ? Theme.of(context).colorScheme.primaryContainer : Theme.of(context).colorScheme.surfaceContainerHighest,
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(isUser ? 'User' : 'Assistant', style: const TextStyle(fontWeight: FontWeight.w700)),
                    const SizedBox(width: 8),
                    IconButton(
                      constraints: const BoxConstraints.tightFor(width: 32, height: 32),
                      padding: EdgeInsets.zero,
                      onPressed: content.isEmpty ? null : () => Clipboard.setData(ClipboardData(text: content)),
                      icon: const Icon(Icons.copy, size: 16),
                      tooltip: '复制',
                    ),
                  ],
                ),
                SelectableText(content),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
