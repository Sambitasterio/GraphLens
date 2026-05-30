"use client";

/**
 * Animated "liquid glass" orb — the self-hosted future.co webm (alpha video),
 * recolored from purple to electric brand blue via a CSS filter. It morphs/
 * rotates on its own (the look the static CSS sphere couldn't reproduce).
 */
export function GlassOrb() {
  return (
    <div className="relative flex items-center justify-center">
      {/* ambient halo behind the orb */}
      <div
        aria-hidden
        className="absolute rounded-full blur-[80px]"
        style={{
          width: "90%",
          height: "90%",
          background:
            "radial-gradient(circle, rgba(0,132,255,0.30) 0%, transparent 66%)",
        }}
      />
      <video
        className="relative w-full max-w-[560px] scale-125"
        style={{
          filter:
            "hue-rotate(-55deg) saturate(250%) brightness(1.2) contrast(1.1)",
        }}
        autoPlay
        loop
        muted
        playsInline
      >
        <source src="/orb.webm" type="video/webm" />
      </video>
    </div>
  );
}
