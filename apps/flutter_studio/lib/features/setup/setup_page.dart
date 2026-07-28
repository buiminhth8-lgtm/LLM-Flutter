import 'package:flutter/material.dart';

class SetupPage extends StatelessWidget {
  const SetupPage({
    super.key,
    required this.passwordController,
    required this.confirmController,
    required this.loading,
    required this.error,
    required this.onInitialize,
    required this.backendStatus,
  });

  final TextEditingController passwordController;
  final TextEditingController confirmController;
  final bool loading;
  final String? error;
  final VoidCallback onInitialize;
  final String backendStatus;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 460),
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text(
                    '初始化 LLM-Studio',
                    style: TextStyle(fontSize: 24, fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    backendStatus,
                    style: const TextStyle(color: Colors.black54),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    '首次使用需要创建本地管理员密码。创建成功后，系统会自动生成首个 API Key 并保存到当前客户端。',
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: passwordController,
                    obscureText: true,
                    decoration: const InputDecoration(
                      labelText: '管理员密码',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: confirmController,
                    obscureText: true,
                    decoration: const InputDecoration(
                      labelText: '确认管理员密码',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  if (error != null) ...[
                    const SizedBox(height: 12),
                    Text(error!, style: const TextStyle(color: Colors.red)),
                  ],
                  const SizedBox(height: 16),
                  FilledButton.icon(
                    onPressed: loading ? null : onInitialize,
                    icon: loading
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.check),
                    label: const Text('初始化'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
