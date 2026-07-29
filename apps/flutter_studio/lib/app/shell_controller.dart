import 'package:flutter/widgets.dart';

class ShellController extends ChangeNotifier {
  ShellController({
    required bool autoRefresh,
    required bool initialRequiresSetup,
  }) : _initialSetupCheckDone = initialRequiresSetup || !autoRefresh,
       _requiresSetup = initialRequiresSetup;

  final setupPasswordController = TextEditingController();
  final setupConfirmController = TextEditingController();

  bool _loading = false;
  bool _initialSetupCheckDone;
  bool _requiresSetup;
  bool _authRequired = false;
  String? _error;

  bool get loading => _loading;
  bool get initialSetupCheckDone => _initialSetupCheckDone;
  bool get requiresSetup => _requiresSetup;
  bool get authRequired => _authRequired;
  String? get error => _error;

  void setLoading(bool value) {
    if (_loading == value) {
      return;
    }
    _loading = value;
    notifyListeners();
  }

  void setInitialSetupCheckDone(bool value) {
    if (_initialSetupCheckDone == value) {
      return;
    }
    _initialSetupCheckDone = value;
    notifyListeners();
  }

  void showSetupRequired() {
    _initialSetupCheckDone = true;
    _requiresSetup = true;
    _authRequired = false;
    _error = null;
    notifyListeners();
  }

  void showAuthenticated({required bool apiKeyMissing}) {
    _initialSetupCheckDone = true;
    _requiresSetup = false;
    _authRequired = apiKeyMissing;
    notifyListeners();
  }

  void completeSetup() {
    _initialSetupCheckDone = true;
    _requiresSetup = false;
    _authRequired = false;
    _error = null;
    notifyListeners();
  }

  void setAuthRequired(String message) {
    _initialSetupCheckDone = true;
    _requiresSetup = false;
    _authRequired = true;
    _error = message;
    notifyListeners();
  }

  void setError(String? message) {
    _initialSetupCheckDone = true;
    _error = message;
    notifyListeners();
  }

  void clearError() => setError(null);

  @override
  void dispose() {
    setupPasswordController.dispose();
    setupConfirmController.dispose();
    super.dispose();
  }
}
