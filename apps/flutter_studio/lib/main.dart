import 'dart:async';
import 'dart:ui';

import 'package:flutter/material.dart';

import 'app/app.dart';
import 'core/logging/client_logger.dart';

export 'app/app.dart';
export 'core/api/api_client.dart';
export 'core/api/api_exception.dart';
export 'core/models/dto.dart';

void main() {
  runZonedGuarded(() {
    WidgetsFlutterBinding.ensureInitialized();
    FlutterError.onError = (details) {
      FlutterError.presentError(details);
      logClientError(details.exception, details.stack);
    };
    PlatformDispatcher.instance.onError = (error, stack) {
      logClientError(error, stack);
      return false;
    };
    logClientInfo('Flutter client starting.');
    runApp(const LlmStudioApp());
  }, logClientError);
}
