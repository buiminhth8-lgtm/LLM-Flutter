import 'package:flutter/widgets.dart';

import '../../core/api/api_client.dart';
import 'rag_state.dart';

class RagController extends ChangeNotifier {
  RagController(this._client);

  final LlmStudioClient _client;
  final queryController = TextEditingController();
  RagState state = const RagState();

  Future<void> query() async {
    final result = await _client.ragQuery(queryController.text.trim());
    state = RagState(result: result);
    notifyListeners();
  }

  @override
  void dispose() {
    queryController.dispose();
    super.dispose();
  }
}
