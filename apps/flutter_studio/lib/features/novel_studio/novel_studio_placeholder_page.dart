import 'package:flutter/material.dart';

class NovelStudioPlaceholderPage extends StatelessWidget {
  const NovelStudioPlaceholderPage({super.key});

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '小说工作台已规划。',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
          ),
          SizedBox(height: 12),
          Text('阶段 0：工程基线准备中。'),
          SizedBox(height: 8),
          Text('下一阶段：Novel 项目与基础资料库。'),
        ],
      ),
    );
  }
}
