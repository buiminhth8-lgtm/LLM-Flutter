import 'package:flutter/material.dart';

import '../../core/ui/app_empty_state.dart';
import '../../core/ui/app_section_header.dart';
import '../../core/ui/app_status_badge.dart';

class BenchmarksPage extends StatelessWidget {
  const BenchmarksPage({
    super.key,
    required this.benchmarks,
    required this.currentModel,
    required this.onStart,
    required this.onRefresh,
  });

  final List<dynamic> benchmarks;
  final Map<String, dynamic>? currentModel;
  final VoidCallback onStart;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    final loaded = currentModel?['loaded'] == true;
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            title: '基准测试',
            subtitle: '实验性功能，仅供本机开发参考；结果受驱动、温度、功耗墙和后台负载影响。',
            actions: [
              const AppStatusBadge(label: '实验性', tone: AppStatusTone.warning),
              const SizedBox(width: 8),
              IconButton.filledTonal(
                onPressed: onRefresh,
                icon: const Icon(Icons.refresh),
                tooltip: '刷新',
              ),
            ],
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: loaded ? onStart : null,
            icon: const Icon(Icons.speed),
            label: const Text('启动当前模型基准测试'),
          ),
          if (!loaded) ...[
            const SizedBox(height: 8),
            Text(
              '请先加载模型。',
              style: TextStyle(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
          ],
          const SizedBox(height: 12),
          Expanded(
            child: benchmarks.isEmpty
                ? const AppEmptyState(
                    title: '没有基准测试报告',
                    message: '加载模型后可启动一次本机参考测试。',
                    icon: Icons.query_stats,
                  )
                : ListView.separated(
                    itemCount: benchmarks.length,
                    separatorBuilder: (_, _) => const Divider(height: 1),
                    itemBuilder: (context, index) {
                      final map = benchmarks[index] is Map
                          ? benchmarks[index] as Map
                          : const {};
                      return ListTile(
                        leading: const Icon(Icons.query_stats),
                        title: Text(
                          '${map['model_id'] ?? map['id'] ?? 'benchmark'}',
                        ),
                        subtitle: Text(
                          [
                            'TTFT: ${map['ttft_seconds'] ?? 'n/a'}',
                            'Token/s: ${map['tokens_per_second'] ?? 'n/a'}',
                            '峰值显存：${map['peak_cuda_reserved'] ?? map['peak_vram'] ?? 'n/a'}',
                            if (map['error'] != null) '错误：${map['error']}',
                          ].join('  '),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
