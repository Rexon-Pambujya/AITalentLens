'use client';

/**
 * ScoreRing - the product's one signature visual element (see docs/design-decisions.md).
 * Rendered as a set of aperture "blades" that close in around the score,
 * echoing "Lens" in the product name, rather than a generic donut chart.
 */
export function ScoreRing({ score, size = 96, label }: { score: number; size?: number; label?: string }) {
  const bladeCount = 12;
  const radius = size / 2 - 8;
  const center = size / 2;
  const activeBlades = Math.round((score / 100) * bladeCount);

  const color = score >= 90 ? '#3F7159' : score >= 75 ? '#3B2FA3' : score >= 60 ? '#C98A2C' : '#B65C43';

  const blades = Array.from({ length: bladeCount }, (_, i) => {
    const angle = (i / bladeCount) * 360 - 90;
    const isActive = i < activeBlades;
    const rad = (angle * Math.PI) / 180;
    const x1 = center + Math.cos(rad) * (radius - 6);
    const y1 = center + Math.sin(rad) * (radius - 6);
    const x2 = center + Math.cos(rad) * radius;
    const y2 = center + Math.sin(rad) * radius;
    return (
      <line
        key={i}
        x1={x1}
        y1={y1}
        x2={x2}
        y2={y2}
        stroke={isActive ? color : '#E3E5EB'}
        strokeWidth={size > 60 ? 3 : 2}
        strokeLinecap="round"
        style={{ transition: 'stroke 300ms ease' }}
      />
    );
  });

  return (
    <div className="inline-flex flex-col items-center gap-1">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {blades}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-mono font-semibold" style={{ fontSize: size / 3.4, color }}>
            {Math.round(score)}
          </span>
        </div>
      </div>
      {label && <span className="text-xs text-ink-faint">{label}</span>}
    </div>
  );
}
