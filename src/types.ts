export type ReactionSfx = 'scratch' | 'impact' | 'whoosh' | 'tick' | 'none';

export type MemeIntent = {
  purpose: 'reaction' | 'punchline' | 'contrast' | 'confusion' | 'failure' | 'success' | 'waiting' | 'absurdity' | 'emphasis';
  tone: 'positive' | 'negative' | 'surprised' | 'confused' | 'awkward' | 'deadpan' | 'chaotic' | 'neutral';
  intensity: 1 | 2 | 3;
  preferredMedia?: 'audio' | 'image' | 'video' | 'any';
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

export type BeatVisualSpec =
  | SourceVisual
  | MetricVisual
  | DiagramVisual
  | ComparisonVisual
  | SymbolVisual
  | TextVisual;

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
};
