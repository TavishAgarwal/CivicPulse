import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';

/// Handles FCM push notifications for volunteer dispatch alerts
class NotificationService {
  final FirebaseMessaging _messaging = FirebaseMessaging.instance;

  Future<void> init() async {
    try {
      // Request notification permissions
      final settings = await _messaging.requestPermission(
        alert: true,
        badge: true,
        sound: true,
        criticalAlert: true,
      );

      if (settings.authorizationStatus == AuthorizationStatus.authorized) {
        debugPrint('[FCM] Notifications authorized');
      } else {
        debugPrint('[FCM] Notifications denied');
      }

      // Get FCM token (will fail on iOS Simulator — that's OK)
      try {
        final token = await _messaging.getToken();
        debugPrint('[FCM] Token: $token');
      } catch (e) {
        debugPrint('[FCM] Token retrieval failed (expected on Simulator): $e');
      }

      // Listen for token refresh
      _messaging.onTokenRefresh.listen((newToken) {
        debugPrint('[FCM] Token refreshed: $newToken');
        // TODO: Save to Firestore volunteer profile
      });

      // Handle foreground messages
      FirebaseMessaging.onMessage.listen((RemoteMessage message) {
        debugPrint('[FCM] Foreground message: ${message.notification?.title}');
        // Notification will be shown by the system on Android
      });

      // Handle notification tap when app was in background
      FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
        debugPrint('[FCM] App opened from notification: ${message.data}');
        // TODO: Navigate to dispatch detail
      });

      // Subscribe to topic for dispatch alerts
      try {
        await _messaging.subscribeToTopic('dispatch_alerts');
        debugPrint('[FCM] Subscribed to dispatch_alerts topic');
      } catch (e) {
        debugPrint('[FCM] Topic subscription failed (expected on Simulator): $e');
      }
    } catch (e) {
      debugPrint('[FCM] Notification init failed (non-fatal): $e');
    }
  }

  Future<String?> getToken() => _messaging.getToken();
}
