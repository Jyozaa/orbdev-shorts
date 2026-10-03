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
  hasAudio?: boolean;
  intentSource?: 'explicit' | 'auto-cue';
};

export type Cutaway = {
  beatIndex: number;
  start: number;
  end: number;
  meme: SelectedMeme;
};

export type SourceAnnotation = {
  label: string;
  x: number;
  y: number;
};

export type SourceVisual = {
  type: 'source';
  sourceIndex: number;
  query: string;
  fit?: 'contain' | 'cover';
  annotations?: SourceAnnotation[];
  src?: string;
  publisher?: string;
  matchScore?: number;
};

export type MetricVisual = {type: 'metric'; value: string};
export type DiagramVisual = {type: 'diagram'; symbols: string[]};
export type ComparisonVisual = {type: 'comparison'; left: string; right: string};
export type SymbolVisual = {type: 'symbol'; symbol: string};
export type TextVisual = {type: 'text'; text: string};

export type LogoVisual = {
  type: 'logo';
  slug: string;
  label?: string;
  src?: string;
};

export type FlowNode =
  | {kind: 'logo'; slug: string; label?: string; src?: string}
  | {kind: 'symbol'; value: string}
  | {kind: 'text'; value: string};

export type FlowVisual = {type: 'flow'; nodes: FlowNode[]};

export type ChartBar = {label: string; value: string; amount: number};
export type ChartVisual = {type: 'chart'; bars: ChartBar[]};

export type TimelinePoint = {label: string; position: number};
export type TimelineVisual = {type: 'timeline'; points: TimelinePoint[]};

export type NetworkVisual = {type: 'network'; center: string; nodes: string[]};

export type ExplainVisual = {
  type: 'explain';
  mode: 'pixel-upscale' | 'network-shrink' | 'capacity' | 'stability' | 'pipeline' | 'fanout';
  labels?: string[];
  stages?: string[];
  fromLayers?: number[];
  toLayers?: number[];
  load?: number;
  center?: string;
  nodes?: string[];
};

export type BeatVisualSpec =
  | SourceVisual
  | MetricVisual
  | DiagramVisual
  | ComparisonVisual
  | SymbolVisual
  | TextVisual
  | LogoVisual
  | FlowVisual
  | ChartVisual
  | TimelineVisual
  | NetworkVisual
  | ExplainVisual;

export type Beat = {
  text: string;
  visual: BeatVisualSpec;
  sfx?: ReactionSfx;
  memeIntent?: MemeIntent;
  start?: number;
  end?: number;
  meme?: SelectedMeme;
};

export type CaptionWord = {text: string; startMs: number; endMs: number};

export type StoryProps = {
  slug: string;
  title: string;
  narration: string;
  durationSeconds: number;
  beats: Beat[];
  visualBeats: Beat[];
  captions: CaptionWord[];
  cutaways: Cutaway[];
};
