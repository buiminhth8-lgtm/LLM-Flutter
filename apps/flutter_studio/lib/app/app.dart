import 'package:flutter/material.dart';

import '../core/api/api_client.dart';
import 'app_shell.dart';
import 'app_theme.dart';

class LlmStudioApp extends StatelessWidget {
  const LlmStudioApp({
    super.key,
    this.autoRefresh = true,
    this.initialRequiresSetup = false,
    this.client,
  });

  final bool autoRefresh;
  final bool initialRequiresSetup;
  final LlmStudioClient? client;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'LLM Studio',
      theme: buildStudioTheme(),
      home: StudioShell(
        autoRefresh: autoRefresh,
        initialRequiresSetup: initialRequiresSetup,
        client: client,
      ),
    );
  }
}
