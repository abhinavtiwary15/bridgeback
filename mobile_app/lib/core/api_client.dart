import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

const String _prefsBaseUrlKey = 'bridgeback_api_base_url';
const String _prefsApiKeyKey = 'bridgeback_api_key';

/// Compile-time default (e.g. `--dart-define=API_URL=https://api.example.com`).
const String _compileTimeApiUrl =
    String.fromEnvironment('API_URL', defaultValue: 'https://bridgeback-api.hf.space');

/// Optional shared gate key matching backend `API_AUTH_TOKEN`.
const String _compileTimeApiKey =
    String.fromEnvironment('API_AUTH_TOKEN', defaultValue: '');

final apiClientProvider = Provider<Dio>((ref) => ApiClient.instance);

class ApiClient {
  static Dio? _dio;

  /// Call once from `main()` before `runApp`.
  static Future<void> ensureInitialized() async {
    if (_dio != null) return;
    final prefs = await SharedPreferences.getInstance();
    final storedUrl = prefs.getString(_prefsBaseUrlKey) ?? '';
    final url = storedUrl.isNotEmpty ? storedUrl : _compileTimeApiUrl;
    _dio = _buildDio(normalizeApiBaseUrl(url));
  }

  static Dio get instance {
    final d = _dio;
    if (d == null) {
      throw StateError('ApiClient.ensureInitialized() was not called in main()');
    }
    return d;
  }

  static bool get hasBaseUrl =>
      _dio != null && _dio!.options.baseUrl.trim().isNotEmpty;

  /// Persist and apply a new API base URL (no trailing slash).
  static Future<void> setBaseUrl(String raw) async {
    await ensureInitialized();
    final normalized = normalizeApiBaseUrl(raw);
    _dio!.options.baseUrl = normalized;
    final prefs = await SharedPreferences.getInstance();
    if (normalized.isEmpty) {
      await prefs.remove(_prefsBaseUrlKey);
    } else {
      await prefs.setString(_prefsBaseUrlKey, normalized);
    }
  }

  /// Optional `x-api-key` when the backend sets `API_AUTH_TOKEN`.
  static Future<void> setApiKey(String? raw) async {
    await ensureInitialized();
    final prefs = await SharedPreferences.getInstance();
    final v = raw?.trim() ?? '';
    if (v.isEmpty) {
      await prefs.remove(_prefsApiKeyKey);
    } else {
      await prefs.setString(_prefsApiKeyKey, v);
    }
  }

  static Future<String?> getStoredBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_prefsBaseUrlKey);
  }

  static Future<String?> getStoredApiKey() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_prefsApiKeyKey);
  }

  static String normalizeApiBaseUrl(String raw) {
    var s = raw.trim();
    if (s.isEmpty) return '';
    while (s.endsWith('/')) {
      s = s.substring(0, s.length - 1);
    }
    if (!s.contains('://')) {
      final local = _looksLikeLocalHost(s);
      s = '${local ? 'http' : 'https'}://$s';
    }
    return s;
  }

  static bool _looksLikeLocalHost(String s) {
    final lower = s.toLowerCase();
    if (lower.startsWith('localhost')) return true;
    if (lower.startsWith('127.')) return true;
    if (RegExp(r'^10\.').hasMatch(s)) return true;
    if (RegExp(r'^192\.168\.').hasMatch(s)) return true;
    final m = RegExp(r'^172\.(1[6-9]|2[0-9]|3[0-1])\.').hasMatch(s);
    return m;
  }

  static Dio _buildDio(String baseUrl) {
    return Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 60),
      ),
    )..interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) async {
            final prefs = await SharedPreferences.getInstance();
            final token = prefs.getString('access_token');
            if (token != null && token.isNotEmpty) {
              options.headers['Authorization'] = 'Bearer $token';
            }
            final apiKey = prefs.getString(_prefsApiKeyKey);
            if (apiKey != null && apiKey.isNotEmpty) {
              options.headers['x-api-key'] = apiKey;
            } else if (_compileTimeApiKey.isNotEmpty) {
              options.headers['x-api-key'] = _compileTimeApiKey;
            }
            return handler.next(options);
          },
        ),
      );
  }
}

extension ApiClientExtensions on Dio {
  Future<Map<String, dynamic>> fetchProgress(String userId) async {
    final response = await get('/progress', queryParameters: {'user_id': userId});
    return response.data as Map<String, dynamic>;
  }
}
