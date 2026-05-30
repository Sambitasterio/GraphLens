"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { ArrowRight } from "lucide-react";

import { GlowBackground } from "@/components/GlowBackground";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { errorMessage, login, signup } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (mode === "signup" && password !== confirm) {
      toast.error("Passwords don't match");
      return;
    }
    setLoading(true);
    try {
      if (mode === "signup") {
        await signup(email, password);
        toast.success("Account created — signing you in…");
      }
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      toast.error(errorMessage(err, "Authentication failed"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-white px-6">
      <GlowBackground />

      <div className="relative z-10 w-full max-w-md">
        <div className="mb-8 text-center">
          <Link href="/" className="font-heading text-2xl font-bold">
            GraphLens
          </Link>
          <p className="mt-2 text-sm text-black/50">
            {mode === "login" ? "Welcome back" : "Create your account"}
          </p>
        </div>

        <div className="glass rounded-[16px] p-8">
          {/* mode toggle */}
          <div className="mb-6 flex rounded-[12px] bg-black/5 p-1 text-sm font-medium">
            {(["login", "signup"] as const).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => {
                  setMode(m);
                  setConfirm("");
                }}
                className={`flex-1 rounded-[9px] py-2 transition-colors ${
                  mode === m ? "bg-white text-black shadow-sm" : "text-black/50"
                }`}
              >
                {m === "login" ? "Sign in" : "Sign up"}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>

            {mode === "signup" && (
              <div className="space-y-1.5">
                <Label htmlFor="confirm">Confirm password</Label>
                <Input
                  id="confirm"
                  type="password"
                  required
                  minLength={6}
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  placeholder="••••••••"
                />
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="glass-cta flex w-full items-center justify-center gap-2 rounded-[12px] py-3 text-sm font-semibold disabled:opacity-60"
            >
              {loading
                ? "Please wait…"
                : mode === "login"
                  ? "Sign in"
                  : "Create account"}
              {!loading && <ArrowRight className="h-4 w-4" />}
            </button>
          </form>
        </div>

        <p className="mt-6 text-center text-xs text-black/40">
          By continuing you agree to the GraphLens terms.
        </p>
      </div>
    </div>
  );
}
