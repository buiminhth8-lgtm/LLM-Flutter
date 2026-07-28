import 'package:flutter/foundation.dart';

import '../../core/api/api_client.dart';
import 'download_state.dart';

class DownloadController extends ChangeNotifier {
  DownloadController(this._client);

  final LlmStudioClient _client;
  DownloadState state = const DownloadState();

  Future<void> refresh() async {
    state = DownloadState(downloads: await _client.downloads());
    notifyListeners();
  }

  Future<void> start({required String repoId, String? revision}) async {
    await _client.startDownload(repoId: repoId, revision: revision);
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
}
