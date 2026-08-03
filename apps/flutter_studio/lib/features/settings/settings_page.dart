import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/models/dto.dart';

class SettingsPage extends StatelessWidget {
  const SettingsPage({
    super.key,
    required this.apiBaseController,
    required this.userIdController,
    required this.apiKeyController,
    required this.localPythonController,
    required this.localBackendRootController,
    required this.backendMode,
    required this.autoStartBackend,
    required this.closeBackendOnExit,
    required this.backendLogs,
    required this.currentUser,
    required this.authUsers,
    required this.loadingAuthUsers,
    required this.onApply,
    required this.onClearAuth,
    required this.onRestartBackend,
    required this.onStopBackend,
    required this.onLoadAuthUsers,
    required this.onRegenerateApiKey,
    required this.onBackendModeChanged,
    required this.onAutoStartChanged,
    required this.onCloseOnExitChanged,
    this.onTestBackend,
    this.onOpenDiagnostics,
    this.onOpenReleaseNotes,
  });

  final TextEditingController apiBaseController;
  final TextEditingController userIdController;
  final TextEditingController apiKeyController;
  final TextEditingController localPythonController;
  final TextEditingController localBackendRootController;
  final String backendMode;
  final bool autoStartBackend;
  final bool closeBackendOnExit;
  final List<String> backendLogs;
  final AuthUserDto? currentUser;
  final List<AuthUserDto> authUsers;
  final bool loadingAuthUsers;
  final VoidCallback onApply;
  final VoidCallback onClearAuth;
  final VoidCallback onRestartBackend;
  final VoidCallback onStopBackend;
  final Future<void> Function() onLoadAuthUsers;
  final Future<RegeneratedApiKeyDto> Function(String userId) onRegenerateApiKey;
  final ValueChanged<String> onBackendModeChanged;
  final ValueChanged<bool> onAutoStartChanged;
  final ValueChanged<bool> onCloseOnExitChanged;
  final VoidCallback? onTestBackend;
  final VoidCallback? onOpenDiagnostics;
  final VoidCallback? onOpenReleaseNotes;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: ListView(
        children: [
          const Text(
            '连接设置',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: apiBaseController,
            decoration: const InputDecoration(
              labelText: 'FastAPI 基础地址',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            children: [
              FilledButton.icon(
                onPressed: onApply,
                icon: const Icon(Icons.check),
                label: const Text('应用'),
              ),
              OutlinedButton.icon(
                onPressed: onClearAuth,
                icon: const Icon(Icons.key_off),
                label: const Text('清除认证'),
              ),
              OutlinedButton.icon(
                onPressed: onRestartBackend,
                icon: const Icon(Icons.restart_alt),
                label: const Text('重启后端'),
              ),
              OutlinedButton.icon(
                onPressed: onStopBackend,
                icon: const Icon(Icons.stop_circle_outlined),
                label: const Text('停止后端'),
              ),
              OutlinedButton.icon(
                onPressed: onTestBackend,
                icon: const Icon(Icons.health_and_safety_outlined),
                label: const Text('测试后端'),
              ),
              OutlinedButton.icon(
                onPressed: onOpenDiagnostics,
                icon: const Icon(Icons.bug_report_outlined),
                label: const Text('诊断'),
              ),
              OutlinedButton.icon(
                onPressed: onOpenReleaseNotes,
                icon: const Icon(Icons.new_releases_outlined),
                label: const Text('发布说明'),
              ),
            ],
          ),
          const SizedBox(height: 16),
          SegmentedButton<String>(
            segments: const [
              ButtonSegment(value: 'local', label: Text('本地后端')),
              ButtonSegment(value: 'remote', label: Text('远程后端')),
            ],
            selected: {backendMode},
            onSelectionChanged: (value) => onBackendModeChanged(value.first),
          ),
          SwitchListTile(
            title: const Text('自动启动本地后端'),
            value: autoStartBackend,
            onChanged: onAutoStartChanged,
          ),
          SwitchListTile(
            title: const Text('退出应用时关闭本地后端'),
            value: closeBackendOnExit,
            onChanged: onCloseOnExitChanged,
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: localPythonController,
                  decoration: const InputDecoration(
                    labelText: '本地 Python 路径',
                    border: OutlineInputBorder(),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextField(
                  controller: localBackendRootController,
                  decoration: const InputDecoration(
                    labelText: '本地后端根目录',
                    border: OutlineInputBorder(),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: userIdController,
                  decoration: const InputDecoration(
                    labelText: '用户 ID（可选）',
                    helperText: '留空则使用 Authorization: Bearer 认证。',
                    border: OutlineInputBorder(),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextField(
                  controller: apiKeyController,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'API Key（X-API-Key）',
                    border: OutlineInputBorder(),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          _AuthRecoverySection(
            currentUser: currentUser,
            authUsers: authUsers,
            loadingAuthUsers: loadingAuthUsers,
            onLoadAuthUsers: onLoadAuthUsers,
            onRegenerateApiKey: onRegenerateApiKey,
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              const Text(
                '后端日志',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
              ),
              const Spacer(),
              OutlinedButton.icon(
                onPressed: backendLogs.isEmpty
                    ? null
                    : () async {
                        await Clipboard.setData(
                          ClipboardData(text: backendLogs.join('\n')),
                        );
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('后端日志已复制。')),
                          );
                        }
                      },
                icon: const Icon(Icons.copy),
                label: const Text('复制日志'),
              ),
            ],
          ),
          const SizedBox(height: 8),
          SizedBox(
            height: 220,
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: const Color(0xff111827),
                borderRadius: BorderRadius.circular(8),
              ),
              child: ListView(
                padding: const EdgeInsets.all(12),
                children: backendLogs.isEmpty
                    ? const [
                        Text(
                          '还没有捕获到后端日志。',
                          style: TextStyle(color: Colors.white70),
                        ),
                      ]
                    : backendLogs
                          .map(
                            (line) => SelectableText(
                              line,
                              style: const TextStyle(
                                color: Colors.white70,
                                fontFamily: 'monospace',
                              ),
                            ),
                          )
                          .toList(),
              ),
            ),
          ),
          const SizedBox(height: 24),
          const Text(
            '小说工作台路线图',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 8),
          const Text('状态：已规划 / 未实现。'),
          const SizedBox(height: 4),
          const Text('阶段 0：工程基线准备中。下一阶段：Novel 项目与基础资料库。'),
        ],
      ),
    );
  }
}

class _AuthRecoverySection extends StatelessWidget {
  const _AuthRecoverySection({
    required this.currentUser,
    required this.authUsers,
    required this.loadingAuthUsers,
    required this.onLoadAuthUsers,
    required this.onRegenerateApiKey,
  });

  final AuthUserDto? currentUser;
  final List<AuthUserDto> authUsers;
  final bool loadingAuthUsers;
  final Future<void> Function() onLoadAuthUsers;
  final Future<RegeneratedApiKeyDto> Function(String userId) onRegenerateApiKey;

  @override
  Widget build(BuildContext context) {
    final isAdmin = currentUser?.isAdmin == true;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '认证恢复',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 8),
        Text(
          currentUser == null
              ? '输入 API Key 后可以留空 User ID，客户端会使用 Bearer-only 认证让后端自动识别用户。'
              : '当前用户：${currentUser!.userId}（${currentUser!.role}）',
        ),
        const SizedBox(height: 8),
        const Text('API Key 不能找回，只能由已认证 admin 重新生成。新 Key 只显示一次。'),
        const SizedBox(height: 12),
        if (isAdmin) ...[
          Row(
            children: [
              OutlinedButton.icon(
                onPressed: loadingAuthUsers ? null : onLoadAuthUsers,
                icon: loadingAuthUsers
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.people_outline),
                label: const Text('加载用户'),
              ),
            ],
          ),
          const SizedBox(height: 8),
          ...authUsers.map(
            (user) => Card(
              child: ListTile(
                title: Text('${user.userId} (${user.role})'),
                subtitle: Text(
                  '已启用=${user.enabled}  Key=${user.apiKeyMasked ?? "***"}',
                ),
                trailing: OutlinedButton.icon(
                  onPressed: () async {
                    final confirmed =
                        await showDialog<bool>(
                          context: context,
                          builder: (dialogContext) => AlertDialog(
                            title: const Text('重新生成 API Key'),
                            content: Text(
                              '即将让 ${user.userId} 的旧 API Key 立即失效。新 Key 只显示一次。',
                            ),
                            actions: [
                              TextButton(
                                onPressed: () =>
                                    Navigator.pop(dialogContext, false),
                                child: const Text('取消'),
                              ),
                              FilledButton(
                                onPressed: () =>
                                    Navigator.pop(dialogContext, true),
                                child: const Text('重新生成'),
                              ),
                            ],
                          ),
                        ) ??
                        false;
                    if (!confirmed || !context.mounted) {
                      return;
                    }
                    final result = await onRegenerateApiKey(user.userId);
                    if (!context.mounted) {
                      return;
                    }
                    await showDialog<void>(
                      context: context,
                      builder: (dialogContext) => AlertDialog(
                        title: const Text('新 API Key'),
                        content: Column(
                          mainAxisSize: MainAxisSize.min,
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('请立即保存。关闭后无法再次查看完整 Key。'),
                            const SizedBox(height: 12),
                            SelectableText(result.apiKey),
                          ],
                        ),
                        actions: [
                          TextButton.icon(
                            onPressed: () async {
                              await Clipboard.setData(
                                ClipboardData(text: result.apiKey),
                              );
                            },
                            icon: const Icon(Icons.copy),
                            label: const Text('复制'),
                          ),
                          FilledButton(
                            onPressed: () => Navigator.pop(dialogContext),
                            child: const Text('关闭'),
                          ),
                        ],
                      ),
                    );
                  },
                  icon: const Icon(Icons.key),
                  label: const Text('重新生成'),
                ),
              ),
            ),
          ),
        ] else
          const Text('用户管理仅 admin 可见。'),
        const SizedBox(height: 12),
        const Text('admin 密码丢失时不能通过远程 UI 重置。请在后端所在机器运行：'),
        const SizedBox(height: 4),
        const SelectableText('python tools/reset_auth.py --reset-admin'),
        const SizedBox(height: 8),
        const Text(
          '如果 admin 密码和 API Key 都丢失，请停止后端，备份并重命名 api_users.json，然后重新初始化。',
        ),
      ],
    );
  }
}
