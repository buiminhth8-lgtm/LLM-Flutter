import 'package:flutter/foundation.dart';

import '../../core/api/api_client.dart';
import 'job_state.dart';

class JobController extends ChangeNotifier {
  JobController(this._client);

  final LlmStudioClient _client;
  JobState state = const JobState();

  Future<void> refresh() async {
    state = JobState(jobs: await _client.jobs());
    notifyListeners();
  }

  Future<void> cancel(String id) async {
    await _client.cancelJob(id);
    await refresh();
  }

  void clear() {
    state = const JobState();
    notifyListeners();
  }
}
