import 'package:build_runner_skill_validation/models/person.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('generated part round-trips JSON', () {
    final person = Person.fromJson({'name': 'Ada'});
    expect(person.toJson()['name'], 'Ada');
  });
}
