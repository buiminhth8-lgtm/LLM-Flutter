class RevisionTag {
  const RevisionTag(this.value, this.label);

  final String value;
  final String label;
}

const revisionTags = [
  RevisionTag('language_polish', '语言润色'),
  RevisionTag('plot_fix', '剧情修正'),
  RevisionTag('character_consistency', '人物一致性'),
  RevisionTag('dialogue_improve', '对白优化'),
  RevisionTag('pacing_adjust', '节奏调整'),
  RevisionTag('detail_expand', '细节补充'),
  RevisionTag('remove_redundancy', '减少废话'),
  RevisionTag('style_unify', '文风统一'),
  RevisionTag('logic_fix', '逻辑修复'),
  RevisionTag('worldbuilding_fix', '世界观修正'),
  RevisionTag('emotion_enhance', '情绪增强'),
  RevisionTag('scene_atmosphere', '氛围增强'),
  RevisionTag('continuity_fix', '连贯性修复'),
  RevisionTag('other', '其他'),
];
