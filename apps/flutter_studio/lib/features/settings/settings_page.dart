import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class SettingsPage extends StatelessWidget {
  const SettingsPage({
    super.key,
    required this.apiBaseController,
    required this.userIdController,
    required this.apiKeyController,
    required this.backendMode,
    required this.autoStartBackend,
    required this.closeBackendOnExit,
    required this.backendLogs,
    required this.onApply,
    required this.onClearAuth,
    required this.onRestartBackend,
    required this.onStopBackend,
    required this.onBackendModeChanged,
    required this.onAutoStartChanged,
    required this.onCloseOnExitChanged,
  });

  final TextEditingController apiBaseController;
  final TextEditingController userIdController;
  final TextEditingController apiKeyController;
  final String backendMode;
  final bool autoStartBackend;
  final bool closeBackendOnExit;
  final List<String> backendLogs;
  final VoidCallback onApply;
  final VoidCallback onClearAuth;
  final VoidCallback onRestartBackend;
  final VoidCallback onStopBackend;
  final ValueChanged<String> onBackendModeChanged;
  final ValueChanged<bool> onAutoStartChanged;
  final ValueChanged<bool> onCloseOnExitChanged;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: ListView(children: [
        const Text('Connection settings', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
        const SizedBox(height: 12),
        TextField(controller: apiBaseController, decoration: const InputDecoration(labelText: 'FastAPI base URL', border: OutlineInputBorder())),
        const SizedBox(height: 12),
        Wrap(spacing: 8, children: [
          FilledButton.icon(onPressed: onApply, icon: const Icon(Icons.check), label: const Text('Apply')),
          OutlinedButton.icon(onPressed: onClearAuth, icon: const Icon(Icons.key_off), label: const Text('Clear auth')),
          OutlinedButton.icon(onPressed: onRestartBackend, icon: const Icon(Icons.restart_alt), label: const Text('Restart backend')),
          OutlinedButton.icon(onPressed: onStopBackend, icon: const Icon(Icons.stop_circle_outlined), label: const Text('Stop backend')),
        ]),
        const SizedBox(height: 16),
        SegmentedButton<String>(
          segments: const [ButtonSegment(value: 'local', label: Text('Local backend')), ButtonSegment(value: 'remote', label: Text('Remote backend'))],
          selected: {backendMode},
          onSelectionChanged: (value) => onBackendModeChanged(value.first),
        ),
        SwitchListTile(title: const Text('Auto-start local backend'), value: autoStartBackend, onChanged: onAutoStartChanged),
        SwitchListTile(title: const Text('Close local backend on app exit'), value: closeBackendOnExit, onChanged: onCloseOnExitChanged),
        const SizedBox(height: 12),
        Row(children: [
          Expanded(child: TextField(controller: userIdController, decoration: const InputDecoration(labelText: 'X-User-ID', border: OutlineInputBorder()))),
          const SizedBox(width: 12),
          Expanded(child: TextField(controller: apiKeyController, obscureText: true, decoration: const InputDecoration(labelText: 'X-API-Key', border: OutlineInputBorder()))),
        ]),
        const SizedBox(height: 16),
        Row(
          children: [
            const Text(
              'Backend logs',
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
                          const SnackBar(
                            content: Text('Backend logs copied.'),
                          ),
                        );
                      }
                    },
              icon: const Icon(Icons.copy),
              label: const Text('Copy logs'),
            ),
          ],
        ),
        const SizedBox(height: 8),
        SizedBox(
          height: 220,
          child: DecoratedBox(
            decoration: BoxDecoration(color: const Color(0xff111827), borderRadius: BorderRadius.circular(8)),
            child: ListView(
              padding: const EdgeInsets.all(12),
              children: backendLogs.isEmpty
                  ? const [Text('No backend logs captured yet.', style: TextStyle(color: Colors.white70))]
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
      ]),
    );
  }
}
