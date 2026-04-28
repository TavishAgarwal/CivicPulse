// File generated from Firebase project civicpulse18
import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;
import 'package:flutter/foundation.dart'
    show defaultTargetPlatform, kIsWeb, TargetPlatform;

class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    if (kIsWeb) {
      throw UnsupportedError('Web platform is not configured.');
    }
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return android;
      case TargetPlatform.iOS:
        return ios;
      default:
        throw UnsupportedError('${defaultTargetPlatform.name} is not supported.');
    }
  }

  static const FirebaseOptions android = FirebaseOptions(
    apiKey: 'AIzaSyBW63FnEz176xhGESuH7MhwMasqeodqN4M',
    appId: '1:921366754305:android:f0747355e069a67299bc00',
    messagingSenderId: '921366754305',
    projectId: 'civicpulse18',
    storageBucket: 'civicpulse18.firebasestorage.app',
  );

  static const FirebaseOptions ios = FirebaseOptions(
    apiKey: 'AIzaSyBW63FnEz176xhGESuH7MhwMasqeodqN4M',
    appId: '1:921366754305:ios:1778fb0ae8b7a16299bc00',
    messagingSenderId: '921366754305',
    projectId: 'civicpulse18',
    storageBucket: 'civicpulse18.firebasestorage.app',
    iosBundleId: 'org.civicpulse.civicpulseVolunteer',
  );
}
