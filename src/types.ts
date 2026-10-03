export type SceneType =
  | 'hook'
  | 'explain'
  | 'comparison'
  | 'impact'
  | 'caveat'
  | 'outro';

export type Scene = {
  type: SceneType;
  start: number;
  end: number;
  kicker?: string;
  title: string;
  body?: string;
  leftTitle?: string;
  leftBody?: string;
  rightTitle?: string;
  rightBody?: string;
};

export type CaptionWord = {
  text: string;
  startMs: number;
  endMs: number;
};

export type StoryProps = {
  slug: string;
  title: string;
  narration: string;
  plannedDurationSeconds: number;
  durationSeconds: number;
  scenes: Scene[];
  captions: CaptionWord[];
};
