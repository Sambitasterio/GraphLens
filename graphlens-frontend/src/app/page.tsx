import Link from "next/link";
import { ArrowRight, Star } from "lucide-react";
import { GlowBackground } from "@/components/GlowBackground";
import { GlassOrb } from "@/components/GlassOrb";
import { Navbar } from "@/components/landing/Navbar";

const TRUSTED = ["Northwind", "Globex", "Initech", "Hooli", "Acme"];

export default function Home() {
  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-white">
      <GlowBackground />

      <div className="relative z-10 mx-auto w-full max-w-[1600px] px-6">
        <Navbar />

        <main className="grid grid-cols-1 items-center gap-8 py-16 md:grid-cols-2 md:py-24">
          {/* Left: hero content */}
          <div className="flex flex-col items-start gap-7">
            {/* Social proof */}
            <div className="flex items-center gap-3 rounded-full glass px-4 py-2">
              <div className="flex">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Star
                    key={i}
                    className="h-4 w-4 fill-[#FF801E] text-[#FF801E]"
                  />
                ))}
              </div>
              <span className="text-sm font-medium text-black/70">
                Rated 4.9/5 by 2700+ customers
              </span>
            </div>

            <h1 className="font-heading text-5xl font-bold leading-[1.05] tracking-[-2px] text-black md:text-[75px]">
              Work smarter,
              <br />
              achieve faster
            </h1>

            <p className="max-w-md text-[18px] leading-relaxed tracking-[-0.5px] text-black/60">
              Upload your documents and get cited, graph-augmented answers from
              an AI that actually reasons across them — not just keyword search.
            </p>

            <Link
              href="/login"
              className="glass-cta group mt-2 flex items-center gap-3 rounded-[16px] py-3 pl-6 pr-3 text-base font-semibold"
            >
              Get Started Now
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-white">
                <ArrowRight className="h-4 w-4 text-[#0084ff] transition-transform group-hover:translate-x-0.5" />
              </span>
            </Link>
          </div>

          {/* Right: glassy orb (decorative — hidden on small screens) */}
          <div className="hidden items-center justify-center md:flex">
            <GlassOrb />
          </div>
        </main>

        {/* Trusted-by footer */}
        <footer className="border-t border-black/5 py-12">
          <p className="mb-8 text-center text-sm font-medium uppercase tracking-wide text-black/40">
            Trusted by top-tier product companies
          </p>
          <div className="flex flex-wrap items-center justify-center gap-x-[100px] gap-y-8 opacity-50 grayscale">
            {TRUSTED.map((name) => (
              <span
                key={name}
                className="font-heading text-2xl font-bold text-black/70"
              >
                {name}
              </span>
            ))}
          </div>
        </footer>
      </div>
    </div>
  );
}
