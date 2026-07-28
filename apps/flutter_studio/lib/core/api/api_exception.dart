class StudioApiException implements Exception {
  StudioApiException(this.message, {this.code, this.statusCode});

  final String message;
  final String? code;
  final int? statusCode;

  @override
  String toString() => code == null ? message : '$code: $message';
}

class AuthRequiredException extends StudioApiException {
  AuthRequiredException(super.message, {String? code, super.statusCode})
      : super(code: code ?? 'AUTH_REQUIRED');
}

class PermissionDeniedException extends StudioApiException {
  PermissionDeniedException(super.message, {String? code, super.statusCode})
      : super(code: code ?? 'PERMISSION_DENIED');
}
