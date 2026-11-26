// The model every build.yaml case in validate.json builds against.
import 'package:json_annotation/json_annotation.dart';

part 'person.g.dart';

@JsonSerializable()
class Person {
  Person({required this.name, this.nickName});

  factory Person.fromJson(Map<String, dynamic> json) => _$PersonFromJson(json);

  final String name;
  final String? nickName;

  Map<String, dynamic> toJson() => _$PersonToJson(this);
}
