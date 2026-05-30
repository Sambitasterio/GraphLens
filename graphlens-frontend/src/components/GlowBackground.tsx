/** Layered blurred-ellipse gradient glow (top-left), per the design spec.
 * Sits at z-0 (above the white page background, below the z-10 content). */
export function GlowBackground() {
  return (
    <div
      aria-hidden
      className="pointer-events-none absolute inset-0 z-0 overflow-hidden"
    >
      <div
        className="absolute -left-40 -top-40 h-[680px] w-[680px] rounded-full blur-[120px]"
        style={{
          background: "radial-gradient(circle, #60B1FF 0%, transparent 70%)",
          opacity: 0.7,
        }}
      />
      <div
        className="absolute left-32 -top-20 h-[560px] w-[560px] rounded-full blur-[120px]"
        style={{
          background: "radial-gradient(circle, #319AFF 0%, transparent 70%)",
          opacity: 0.55,
        }}
      />
    </div>
  );
}
