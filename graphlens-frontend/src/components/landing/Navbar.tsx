import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

const NAV_LINKS = [
  { label: "Home", href: "/" },
  { label: "Features", href: "#features" },
  { label: "Company", href: "#company" },
  { label: "Pricing", href: "#pricing" },
];

export function Navbar() {
  return (
    <header className="sticky top-[30px] z-50 mx-auto flex w-fit items-center gap-8 rounded-[16px] glass px-5 py-3">
      <Link href="/" className="font-heading text-xl font-bold tracking-tight">
        GraphLens
      </Link>

      <nav className="hidden items-center gap-6 md:flex">
        {NAV_LINKS.map((link) => (
          <Link
            key={link.label}
            href={link.href}
            className="text-sm font-medium text-black/70 transition-colors hover:text-black"
          >
            {link.label}
          </Link>
        ))}
      </nav>

      <Link
        href="/login"
        className="glass-cta flex items-center gap-1.5 rounded-[12px] px-4 py-2 text-sm font-semibold"
      >
        Sign Up
        <ArrowUpRight className="h-4 w-4" />
      </Link>
    </header>
  );
}
