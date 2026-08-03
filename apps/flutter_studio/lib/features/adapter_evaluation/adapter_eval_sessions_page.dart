import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/ui/app_section_header.dart';
import 'adapter_compare_page.dart';
import 'adapter_eval_controller.dart';
import 'adapter_eval_session_detail_page.dart';
import 'models/adapter_eval_create_request_dto.dart';
import 'widgets/adapter_eval_create_session_dialog.dart';
import 'widgets/adapter_eval_session_list.dart';

class AdapterEvalSessionsPage extends StatefulWidget {
  const AdapterEvalSessionsPage({
    super.key,
    required this.controller,
    this.onOpenFullEvaluation,
  });

  final AdapterEvalController controller;
  final ValueChanged<String>? onOpenFullEvaluation;

  @override
  State<AdapterEvalSessionsPage> createState() =>
      _AdapterEvalSessionsPageState();
}

class _AdapterEvalSessionsPageState extends State<AdapterEvalSessionsPage> {
  @override
  void initState() {
    super.initState();
    if (widget.controller.state.sessions.isEmpty) {
      unawaited(widget.controller.refresh());
    }
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
    animation: widget.controller,
    builder: (context, _) {
      final state = widget.controller.state;
      return Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AppSectionHeader(
              title: '适配器评估',
              subtitle: '阶段 9：同一提示下对比基础模型与适配器输出，人工评分并生成轻量报告。',
              actions: [
                OutlinedButton.icon(
                  key: const Key('adapter-eval-open-full-evaluation'),
                  onPressed:
                      state.currentSession == null ||
                          widget.onOpenFullEvaluation == null
                      ? null
                      : () => widget.onOpenFullEvaluation?.call(
                          state.currentSession!.sessionId,
                        ),
                  icon: const Icon(Icons.fact_check_outlined),
                  label: const Text('打开完整评估'),
                ),
                FilledButton.icon(
                  key: const Key('adapter-eval-new-session'),
                  onPressed: state.loading ? null : _showCreateSession,
                  icon: const Icon(Icons.add_chart_outlined),
                  label: const Text('新建会话'),
                ),
                IconButton.filledTonal(
                  onPressed: state.loading ? null : widget.controller.refresh,
                  icon: const Icon(Icons.refresh),
                  tooltip: '刷新',
                ),
              ],
            ),
            if (state.loading) const LinearProgressIndicator(),
            if (state.error != null)
              MaterialBanner(
                content: Text(state.error!),
                leading: const Icon(Icons.error_outline),
                actions: const [SizedBox.shrink()],
              ),
            if (state.notice != null)
              MaterialBanner(
                content: Text(state.notice!),
                leading: const Icon(Icons.info_outline),
                actions: const [SizedBox.shrink()],
              ),
            const SizedBox(height: 12),
            Expanded(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  SizedBox(
                    width: 310,
                    child: AdapterEvalSessionList(
                      sessions: state.sessions,
                      onSelect: widget.controller.selectSession,
                    ),
                  ),
                  const VerticalDivider(width: 24),
                  Expanded(
                    child: AdapterEvalSessionDetailPage(
                      controller: widget.controller,
                    ),
                  ),
                  const VerticalDivider(width: 24),
                  SizedBox(
                    width: 430,
                    child: AdapterComparePage(controller: widget.controller),
                  ),
                ],
              ),
            ),
          ],
        ),
      );
    },
  );

  void _showCreateSession() {
    showDialog<void>(
      context: context,
      builder: (_) => AdapterEvalCreateSessionDialog(
        onCreate: (CreateAdapterEvalSessionRequest request) {
          unawaited(widget.controller.createSession(request));
        },
      ),
    );
  }
}
