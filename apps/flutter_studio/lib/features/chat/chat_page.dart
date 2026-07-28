import 'package:flutter/material.dart';

import '../../core/models/dto.dart';
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
    final adapter = currentModel?['adapter_id'] ?? currentModel?['adapter'];
    final canChat = modelId.isNotEmpty && loaded && !controller.isGenerating;
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  loaded ? 'Current model: $modelId${adapter == null ? '' : '  Adapter: $adapter'}' : 'Please load a model on the Models page.',
                  style: const TextStyle(fontWeight: FontWeight.w700),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const Text('Stream'),
              Switch(value: controller.streamingEnabled, onChanged: controller.isGenerating ? null : onStreamingChanged),
            ],
          ),
          const SizedBox(height: 12),
          TextField(controller: systemController, enabled: loaded, decoration: const InputDecoration(labelText: 'System Prompt', border: OutlineInputBorder())),
          const SizedBox(height: 12),
          Expanded(
            child: DecoratedBox(
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(8)),
              child: controller.turns.isEmpty
                  ? const Center(child: Text('Start a multi-turn chat.'))
                  : ListView.builder(
                      padding: const EdgeInsets.all(12),
                      itemCount: controller.turns.length,
                      itemBuilder: (context, index) {
                        final ChatTurn turn = controller.turns[index];
                        final isUser = turn.role == 'user';
                        return Align(
                          alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                          child: ConstrainedBox(
                            constraints: const BoxConstraints(maxWidth: 760),
                            child: Card(
                              color: isUser ? const Color(0xffdbeafe) : const Color(0xfff1f5f9),
                              child: Padding(padding: const EdgeInsets.all(12), child: SelectableText(turn.content.isEmpty && controller.isGenerating ? 'Generating...' : turn.content)),
                            ),
                          ),
                        );
                      },
                    ),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: inputController,
                  enabled: canChat,
                  minLines: 1,
                  maxLines: 4,
                  decoration: const InputDecoration(hintText: 'Message', border: OutlineInputBorder()),
                  onSubmitted: (_) {
                    if (canChat) {
                      onSend();
                    }
                  },
                ),
              ),
              const SizedBox(width: 8),
              IconButton.filledTonal(onPressed: onClear, icon: const Icon(Icons.delete_outline), tooltip: 'Clear'),
              const SizedBox(width: 8),
              IconButton.filledTonal(onPressed: controller.turns.any((turn) => turn.role == 'user') && !controller.isGenerating ? onRegenerate : null, icon: const Icon(Icons.refresh), tooltip: 'Regenerate'),
              const SizedBox(width: 8),
              if (controller.isGenerating)
                FilledButton.icon(onPressed: onStop, icon: const Icon(Icons.stop), label: const Text('Stop'))
              else
                FilledButton.icon(onPressed: canChat ? onSend : null, icon: const Icon(Icons.send), label: const Text('Send')),
            ],
          ),
        ],
      ),
    );
  }
}
