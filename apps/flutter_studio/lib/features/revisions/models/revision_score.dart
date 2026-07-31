class RevisionScore {
  const RevisionScore(this.value, this.label);

  final int value;
  final String label;
}

const revisionScores = [
  RevisionScore(1, '1 很差'),
  RevisionScore(2, '2 较差'),
  RevisionScore(3, '3 可用'),
  RevisionScore(4, '4 较好'),
  RevisionScore(5, '5 很好'),
];
