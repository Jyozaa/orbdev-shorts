export type ReactionSfx = 'scratch' | 'impact' | 'whoosh' | 'tick' | 'none';

export type MemePresentation = 'auto' | 'overlay' | 'cutaway';

export type MemeIntent = {
  purpose: 'reaction' | 'punchline' | 'contrast' | 'confusion' | 'failure' | 'success' | 'waiting' | 'absurdity' | 'emphasis';
  tone: 'positive' | 'negative' | 'surprised' | 'confused' | 'awkward' | 'deadpan' | 'chaotic' | 'neutral';
  intensity: 1 | 2 | 3;
  preferredMedia?: 'audio' | 'image' | 'video' | 'any';
  presentation?: MemePresentation;
  maxDurationSeconds?: number;
  concepts?: string[];
};

export type SelectedMeme = {
  id: string;
  mediaType: 'audio' | 'image' | 'video';
  src: string;
  durationSeconds: number;
  offsetSeconds: number;
  volume?: number;
  presentation: 'overlay' | 'cutaway';
  sourceDurationSeconds?: number;
  completeClip?: boolean;
};

export type Cutaway = {
  beatIndex: number;
  start: number;
  end: number;
  meme: SelectedMeme;
};

export type SourceVisual = {
  type: 'source';
  sourceIndex: number;
  src?: string;
  publisher?: string;
};

export type MetricVisual = {
  type: 'metric';
  value: string;
};

export type DiagramVisual = {
  type: 'diagram';
  symbols: string[];
};

export type ComparisonVisual = {
  type: 'comparison';
  left: string;
  right: string;
};

export type SymbolVisual = {
  type: 'symbol';
  symbol: string;
};

export type TextVisual = {
  type: 'text';
  text: string;
};

export type LogoVisual = {
  type: 'logo';
  slug: string;
  label?: string;
  src?: string;
};

export type FlowNode =
  | {
      kind: 'logo';
      slug: string;
      label?: string;
      src?: string;
    }
  | {
      kind: 'symbol';
      value: string;
    }
  | {
      kind: 'text';
      value: string;
    };

export type FlowVisual = {
  type: 'flow';
  nodes: FlowNode[];
};

export type BeatVisualSpec =
  | SourceVisual
  | MetricVisual
  | DiagramVisual
  | ComparisonVisual
  | SymbolVisual
  | TextVisual
  | LogoVisual
  | FlowVisual;

export type Beat = {
  text: string;
  visual: BeatVisualSpec;
  sfx?: ReactionSfx;
  memeIntent?: MemeIntent;
  start?: number;
  end?: number;
  meme?: SelectedMeme;
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
  durationSeconds: number;
  beats: Beat[];
  captions: CaptionWord[];
  cutaways: Cutaway[];
};
