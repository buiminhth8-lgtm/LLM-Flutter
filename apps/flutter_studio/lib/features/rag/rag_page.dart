import 'package:flutter/material.dart';

import '../../core/ui/app_empty_state.dart';
import '../../core/ui/app_section_header.dart';
import '../../core/ui/app_status_badge.dart';

class RagPage extends StatelessWidget {
  const RagPage({
    super.key,
    required this.queryController,
    required this.result,
    required this.onQuery,
  });

  final TextEditingController queryController;
  final String? result;
  final VoidCallback onQuery;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const AppSectionHeader(
            title: 'RAG',
            subtitle:
                '当前 Flutter 页面提供最小查询测试面。文档上传和索引重建由后台 Job 处理；本地 file_path / directory_path 入口默认隐藏。',
            actions: [
              AppStatusBadge(label: '本地路径受限', tone: AppStatusTone.warning),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: queryController,
                  decoration: const InputDecoration(
                    labelText: 'RAG 问题',
                    helperText: '请求体字段使用 question，默认 top_k=5。',
                    border: OutlineInputBorder(),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              FilledButton.icon(
                onPressed: onQuery,
                icon: const Icon(Icons.search),
                label: const Text('查询'),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Expanded(
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: result == null || result!.isEmpty
                    ? const AppEmptyState(
                        title: '没有查询结果',
                        message: '索引不存在时，请先通过后端导入文档并重建索引。',
                        icon: Icons.article_outlined,
                      )
                    : SingleChildScrollView(child: SelectableText(result!)),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
