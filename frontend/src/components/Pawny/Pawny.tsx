export type Mood = "idle" | "hit" | "scanning" | "safe" | "phishy" | "miss";

const INK = "#2B2350";
const BODY = "#7CB5F8";
const SHADE = "#5E9CE8";
const DEEP = "#4E8FD9";

const LABELS: Record<Mood, string> = {
  idle: "Pawny, waiting for a link",
  hit: "Pawny, slamming his loupe down on the link",
  scanning: "Pawny, reading the link through a magnifier",
  safe: "Pawny, smiling with a thumbs up",
  phishy: "Pawny, alarmed with hands up",
  miss: "Pawny, embarrassed and scratching his head",
};

const BODY_CLASS: Record<Mood, string> = {
  idle: "",
  hit: "",
  scanning: "pw-bob",
  safe: "pw-pop",
  phishy: "pw-pop",
  miss: "pw-pop",
};

function HeadLoupe() {
  return <circle cx="152" cy="34" r="13" fill="#F9F8F3" stroke="#F7B951" strokeWidth="7" />;
}

function Arm({ cx, cy, rotate = 0 }: { cx: number; cy: number; rotate?: number }) {
  return (
    <ellipse
      cx={cx}
      cy={cy}
      rx="11"
      ry="17"
      fill={SHADE}
      transform={rotate ? `rotate(${rotate} ${cx} ${cy})` : undefined}
    />
  );
}

function Face({ mood }: { mood: Mood }) {
  switch (mood) {
    case "idle":
      return (
        <>
          <HeadLoupe />
          <g className="pw-blink">
            <ellipse cx="98" cy="84" rx="14" ry="16" fill="#FFFFFF" />
            <ellipse cx="142" cy="84" rx="14" ry="16" fill="#FFFFFF" />
            <circle cx="100" cy="88" r="7.5" fill={INK} />
            <circle cx="144" cy="88" r="7.5" fill={INK} />
            <circle cx="102.5" cy="85" r="2.5" fill="#FFFFFF" />
            <circle cx="146.5" cy="85" r="2.5" fill="#FFFFFF" />
          </g>
          <path d="M108 114 Q120 126 132 114" fill="none" stroke={INK} strokeWidth="5" strokeLinecap="round" />
          <Arm cx={80} cy={192} />
          <Arm cx={160} cy={192} />
        </>
      );
    case "hit":
      return (
        <>
          <path d="M84 64 L108 74" stroke={INK} strokeWidth="6" strokeLinecap="round" />
          <path d="M156 64 L132 74" stroke={INK} strokeWidth="6" strokeLinecap="round" />
          <ellipse cx="98" cy="88" rx="13" ry="11" fill="#FFFFFF" />
          <ellipse cx="142" cy="88" rx="13" ry="11" fill="#FFFFFF" />
          <circle cx="100" cy="90" r="6" fill={INK} />
          <circle cx="140" cy="90" r="6" fill={INK} />
          <rect x="104" y="112" width="32" height="12" rx="6" fill="#FFFFFF" stroke={INK} strokeWidth="4" />
          <ellipse cx="74" cy="44" rx="12" ry="18" fill={SHADE} transform="rotate(-30 74 44)" />
          <ellipse cx="166" cy="44" rx="12" ry="18" fill={SHADE} transform="rotate(30 166 44)" />
          <circle cx="120" cy="20" r="15" fill="#F9F8F3" stroke="#F7B951" strokeWidth="8" />
        </>
      );
    case "scanning":
      return (
        <>
          <HeadLoupe />
          <path d="M82 66 L106 70" stroke={INK} strokeWidth="5" strokeLinecap="round" />
          <ellipse cx="98" cy="86" rx="13" ry="15" fill="#FFFFFF" />
          <circle cx="94" cy="92" r="7" fill={INK} />
          <ellipse cx="142" cy="86" rx="14" ry="16" fill="#FFFFFF" />
          <circle cx="138" cy="93" r="10" fill={INK} />
          <circle cx="141" cy="89" r="3" fill="#FFFFFF" />
          <ellipse cx="120" cy="120" rx="6" ry="7" fill={INK} />
          <g className="pw-scan">
            <path d="M160 106 L190 150" stroke="#D9962E" strokeWidth="11" strokeLinecap="round" />
            <circle cx="142" cy="86" r="25" fill="#F9F8F3" fillOpacity="0.35" stroke="#F7B951" strokeWidth="9" />
            <ellipse cx="192" cy="154" rx="12" ry="15" fill={SHADE} />
          </g>
          <Arm cx={80} cy={192} />
        </>
      );
    case "safe":
      return (
        <>
          <path d="M86 90 Q98 74 110 90" fill="none" stroke={INK} strokeWidth="6" strokeLinecap="round" />
          <path d="M130 90 Q142 74 154 90" fill="none" stroke={INK} strokeWidth="6" strokeLinecap="round" />
          <path d="M100 106 Q120 138 140 106 Z" fill={INK} />
          <path d="M110 120 Q120 130 130 120 Q120 116 110 120 Z" fill="#FF8585" />
          <Arm cx={80} cy={192} />
          <ellipse cx="184" cy="132" rx="12" ry="18" fill={SHADE} transform="rotate(30 184 132)" />
          <HeadLoupe />
        </>
      );
    case "phishy":
      return (
        <>
          <path d="M84 70 L108 60" stroke={INK} strokeWidth="5" strokeLinecap="round" />
          <path d="M156 70 L132 60" stroke={INK} strokeWidth="5" strokeLinecap="round" />
          <ellipse cx="98" cy="88" rx="16" ry="18" fill="#FFFFFF" />
          <ellipse cx="142" cy="88" rx="16" ry="18" fill="#FFFFFF" />
          <circle cx="98" cy="90" r="4.5" fill={INK} />
          <circle cx="142" cy="90" r="4.5" fill={INK} />
          <path
            d="M102 122 Q108 114 114 122 Q120 130 126 122 Q132 114 138 122"
            fill="none"
            stroke={INK}
            strokeWidth="5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <HeadLoupe />
          <path d="M166 58 Q159 71 166 76 Q173 71 166 58 Z" fill="#FFFFFF" />
          <ellipse cx="58" cy="148" rx="12" ry="18" fill={SHADE} transform="rotate(-25 58 148)" />
          <ellipse cx="182" cy="148" rx="12" ry="18" fill={SHADE} transform="rotate(25 182 148)" />
        </>
      );
    case "miss":
      return (
        <>
          <path d="M86 88 L110 88" stroke={INK} strokeWidth="6" strokeLinecap="round" />
          <ellipse cx="142" cy="86" rx="14" ry="16" fill="#FFFFFF" />
          <circle cx="150" cy="84" r="7.5" fill={INK} />
          <path d="M130 66 L154 62" stroke={INK} strokeWidth="5" strokeLinecap="round" />
          <path d="M106 120 Q120 126 136 112" fill="none" stroke={INK} strokeWidth="5" strokeLinecap="round" />
          <Arm cx={80} cy={192} />
          <ellipse cx="172" cy="64" rx="12" ry="17" fill={SHADE} transform="rotate(-35 172 64)" />
          <HeadLoupe />
        </>
      );
  }
}

type Props = {
  mood?: Mood;
  size?: number;
  /** Decorative copies (the logo) are hidden from screen readers. */
  decorative?: boolean;
};

export function Pawny({ mood = "idle", size = 240, decorative = false }: Props) {
  const blush = mood === "safe" || mood === "miss";
  return (
    <svg
      viewBox="0 0 240 288"
      width={size}
      height={Math.round(size * 1.2)}
      role={decorative ? undefined : "img"}
      aria-label={decorative ? undefined : LABELS[mood]}
      aria-hidden={decorative || undefined}
      style={{ display: "block", overflow: "visible" }}
    >
      <ellipse cx="120" cy="274" rx="72" ry="9" fill={INK} opacity="0.12" />
      {/* key restarts the pop animation every time the mood changes */}
      <g key={mood} className={BODY_CLASS[mood] || undefined}>
        <rect x="50" y="236" width="140" height="34" rx="17" fill={DEEP} />
        <rect x="50" y="234" width="140" height="26" rx="13" fill={BODY} />
        <path d="M90 150 C94 190 82 220 66 240 L174 240 C158 220 146 190 150 150 Z" fill={BODY} />
        <path d="M140 150 C144 190 150 220 164 240 L174 240 C158 220 146 190 150 150 Z" fill={SHADE} />
        <rect x="74" y="140" width="92" height="20" rx="10" fill={DEEP} />
        <circle cx="120" cy="86" r="58" fill={BODY} />
        <path d="M150 38 A58 58 0 0 1 150 134 A70 70 0 0 0 150 38 Z" fill={SHADE} />
        {blush && (
          <>
            <circle cx="86" cy="110" r="9" fill="#FF8585" opacity="0.55" />
            <circle cx="154" cy="110" r="9" fill="#FF8585" opacity="0.55" />
          </>
        )}
        <Face mood={mood} />
      </g>
    </svg>
  );
}
