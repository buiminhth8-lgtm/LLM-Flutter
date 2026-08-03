import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

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
      locale: const Locale('zh', 'CN'),
      supportedLocales: const [Locale('zh', 'CN'), Locale('en', 'US')],
      localizationsDelegates: GlobalMaterialLocalizations.delegates,
      theme: buildStudioTheme(),
      home: StudioShell(
        autoRefresh: autoRefresh,
        initialRequiresSetup: initialRequiresSetup,
        client: client,
      ),
    );
  }
}
