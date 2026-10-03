export type SceneType =
  | 'hook'
  | 'explain'
  | 'metric'
  | 'diagram'
  | 'comparison'
  | 'impact'
  | 'caveat'
  | 'outro';

export type ReactionSfx =
  | 'yay'
  | 'rage'
  | 'scratch'
  | 'impact'
  | 'whoosh'
  | 'tick'
  | 'none';

export type DiagramNode = {
  symbol: string;
  label?: string;
};

export type Scene = {
  type: SceneType;
  start: number;
  end: number;
  kicker?: string;
  title: string;
  body?: string;
  leftTitle?: string;
  leftBody?: string;
  leftSymbol?: string;
  rightTitle?: string;
  rightBody?: string;
  rightSymbol?: string;
  nodes?: DiagramNode[];
  sfx?: ReactionSfx;
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
