import 'dart:async';

import 'package:flutter/foundation.dart';

import '../../core/api/api_client.dart';
import 'download_state.dart';

class DownloadController extends ChangeNotifier {
  DownloadController(this._client);

  final LlmStudioClient _client;
  DownloadState state = const DownloadState();
  Timer? _pollTimer;
  bool _refreshing = false;

  Future<void> refresh() async {
    if (_refreshing) {
      return;
    }
    _refreshing = true;
    try {
      state = DownloadState(downloads: await _client.downloads());
      _syncPolling();
      notifyListeners();
    } finally {
      _refreshing = false;
    }
  }

  Future<void> start({
    required String repoId,
    String provider = 'huggingface',
    String? revision,
    List<String>? allowPatterns,
    List<String>? ignorePatterns,
  }) async {
    await _client.startDownload(
      repoId: repoId,
      provider: provider,
      revision: revision,
      allowPatterns: allowPatterns,
      ignorePatterns: ignorePatterns,
    );
    await refresh();
  }

  Future<void> cancel(String id) async {
    await _client.cancelDownload(id);
    await refresh();
  }

  Future<void> retry(String id) async {
    await _client.retryDownload(id);
    await refresh();
  }

  Future<void> deleteRecord(String id) async {
    await _client.deleteDownloadRecord(id);
    await refresh();
  }

  void _syncPolling() {
    if (state.hasRunningDownloads) {
      _pollTimer ??= Timer.periodic(const Duration(seconds: 1), (_) {
        unawaited(refresh());
      });
    } else {
      _pollTimer?.cancel();
      _pollTimer = null;
    }
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }
}
