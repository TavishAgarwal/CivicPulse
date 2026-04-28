import 'package:cloud_firestore/cloud_firestore.dart';

class FirestoreService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  // ── Wards ────────────────────────────────────────────
  Stream<List<Map<String, dynamic>>> watchWards({String cityId = 'delhi'}) {
    return _db
        .collection('cities')
        .doc(cityId)
        .collection('wards')
        .orderBy('css', descending: true)
        .snapshots()
        .map((snap) => snap.docs.map((d) {
              final data = d.data();
              data['id'] = d.id;
              return data;
            }).toList());
  }

  Future<Map<String, dynamic>?> getWard(String wardId,
      {String cityId = 'delhi'}) async {
    final doc = await _db
        .collection('cities')
        .doc(cityId)
        .collection('wards')
        .doc(wardId)
        .get();
    if (!doc.exists) return null;
    final data = doc.data()!;
    data['id'] = doc.id;
    return data;
  }

  // ── Dispatches ───────────────────────────────────────
  Stream<List<Map<String, dynamic>>> watchDispatches(
      {String? volunteerId}) {
    Query<Map<String, dynamic>> query =
        _db.collection('dispatches').orderBy('createdAt', descending: true);
    if (volunteerId != null) {
      query = query.where('volunteerId', isEqualTo: volunteerId);
    }
    return query.limit(50).snapshots().map((snap) => snap.docs.map((d) {
          final data = d.data();
          data['id'] = d.id;
          return data;
        }).toList());
  }

  Future<void> updateDispatchStatus(
      String dispatchId, String newStatus) async {
    await _db.collection('dispatches').doc(dispatchId).update({
      'status': newStatus,
      'updatedAt': FieldValue.serverTimestamp(),
    });
  }

  // ── Volunteers ───────────────────────────────────────
  Future<Map<String, dynamic>?> getVolunteerProfile(
      String volunteerId) async {
    final doc =
        await _db.collection('volunteers').doc(volunteerId).get();
    if (!doc.exists) return null;
    final data = doc.data()!;
    data['id'] = doc.id;
    return data;
  }

  Stream<Map<String, dynamic>?> watchVolunteerProfile(
      String volunteerId) {
    return _db
        .collection('volunteers')
        .doc(volunteerId)
        .snapshots()
        .map((doc) {
      if (!doc.exists) return null;
      final data = doc.data()!;
      data['id'] = doc.id;
      return data;
    });
  }

  Future<void> updateVolunteerFatigue(
      String volunteerId, double fatigue) async {
    await _db.collection('volunteers').doc(volunteerId).update({
      'fatigue_score': fatigue,
    });
  }

  // ── Ward CSS History ─────────────────────────────────
  Future<List<Map<String, dynamic>>> getWardCSSHistory(String wardId,
      {String cityId = 'delhi', int limit = 14}) async {
    final snap = await _db
        .collection('cities')
        .doc(cityId)
        .collection('wards')
        .doc(wardId)
        .collection('cssHistory')
        .orderBy('date', descending: true)
        .limit(limit)
        .get();
    return snap.docs.map((d) {
      final data = d.data();
      data['id'] = d.id;
      return data;
    }).toList();
  }
}
