class ChatTurn {
  const ChatTurn({required this.role, required this.content});

  factory ChatTurn.user(String content) => ChatTurn(role: 'user', content: content);

  factory ChatTurn.assistant(String content) => ChatTurn(role: 'assistant', content: content);

  final String role;
  final String content;

  ChatTurn copyWith({String? role, String? content}) {
    return ChatTurn(role: role ?? this.role, content: content ?? this.content);
  }
}

class CurrentModelState {
  const CurrentModelState({required this.loaded, this.modelId, this.displayName, this.adapterId});

  factory CurrentModelState.fromMap(Map<String, dynamic>? map) {
    if (map == null || map['loaded'] != true) {
      return const CurrentModelState(loaded: false);
    }
    return CurrentModelState(
      loaded: true,
      modelId: '${map['model_id'] ?? ''}',
      displayName: '${map['display_name'] ?? map['model_id'] ?? ''}',
      adapterId: map['adapter_id'] == null ? null : '${map['adapter_id']}',
    );
  }

  final bool loaded;
  final String? modelId;
  final String? displayName;
  final String? adapterId;
}
