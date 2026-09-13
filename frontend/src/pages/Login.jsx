import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/**
 * Full-bleed split screen — this page renders its own background/height and
 * is not meant to sit inside <Layout>'s nav+main chrome. In App.jsx, the
 * /login route should render <Login /> directly, not
 * <Layout><Login /></Layout>, or the illustration panel will be competing
 * with the nav bar for vertical space.
 */

function ShowcasePanel() {
  return (
    <div className="relative hidden overflow-hidden bg-brand-900 lg:flex lg:flex-col lg:justify-between lg:p-10">
      <svg
        viewBox="0 0 400 500"
        preserveAspectRatio="xMidYMax slice"
        className="pointer-events-none absolute inset-0 h-full w-full"
        aria-hidden="true"
      >
        <defs>
          <radialGradient id="sunGlow" cx="78%" cy="18%" r="45%">
            <stop offset="0%" stopColor="var(--color-brand-400)" stopOpacity="0.35" />
            <stop offset="100%" stopColor="var(--color-brand-400)" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* soft sun glow, upper right */}
        <rect width="400" height="500" fill="url(#sunGlow)" />
        <circle cx="312" cy="90" r="34" className="fill-brand-400" fillOpacity="0.5" />

        {/* rolling hills, back to front */}
        <path d="M0,300 Q100,260 200,285 T400,270 V500 H0 Z" className="fill-brand-800" />
        <path d="M0,350 Q120,310 220,335 T400,320 V500 H0 Z" className="fill-brand-700" fillOpacity="0.8" />

        {/* scattered sampling-point markers, echoing the Map Explorer's
            district survey points */}
        <circle cx="70" cy="230" r="3" className="fill-brand-100" fillOpacity="0.6" />
        <circle cx="140" cy="200" r="3" className="fill-brand-100" fillOpacity="0.4" />
        <circle cx="260" cy="215" r="3" className="fill-brand-100" fillOpacity="0.5" />
        <circle cx="330" cy="190" r="3" className="fill-brand-100" fillOpacity="0.35" />
        <path
          d="M70,230 L140,200 L260,215 L330,190"
          className="stroke-brand-100"
          strokeOpacity="0.25"
          strokeWidth="1"
          strokeDasharray="3 5"
          fill="none"
        />

        {/* central tree — trunk */}
        <path d="M195,360 L192,270 Q200,262 208,270 L205,360 Z" className="fill-soil-700" />

        {/* canopy, three overlapping layers for depth */}
        <circle cx="200" cy="235" r="52" className="fill-brand-800" />
        <circle cx="172" cy="250" r="44" className="fill-brand-600" />
        <circle cx="228" cy="248" r="44" className="fill-brand-600" />
        <circle cx="200" cy="215" r="46" className="fill-brand-500" />
        <circle cx="185" cy="205" r="20" className="fill-brand-400" fillOpacity="0.7" />
      </svg>

      <div className="relative">
        <p className="font-[var(--font-display)] text-lg font-semibold text-parchment-50">
          Tree Plantation AI
        </p>
      </div>

      <div className="relative max-w-sm">
        <h2 className="font-[var(--font-display)] text-2xl font-semibold leading-tight text-parchment-50">
          Climate-resilient tree recommendations for Mandi Bahauddin
        </h2>
        <ul className="mt-5 space-y-2.5 text-sm text-brand-100">
          <li className="flex items-start gap-2">
            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-brand-400" />
            Grounded in retrieved evidence, not guesses
          </li>
          <li className="flex items-start gap-2">
            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-brand-400" />
            Live soil and climate data for the exact point you pick
          </li>
          <li className="flex items-start gap-2">
            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-brand-400" />
            Every answer traces back to a real, citable source
          </li>
        </ul>
      </div>
    </div>
  );
}

export default function Login() {
  const { signInWithPassword, signUp, signInWithGoogle } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTo = location.state?.from?.pathname || "/assistant";

  const [mode, setMode] = useState("signin"); // "signin" | "signup"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      if (mode === "signup") {
        await signUp(email, password);
      } else {
        await signInWithPassword(email, password);
      }
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(err.message || "Something went wrong. Try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleGoogle = async () => {
    setError(null);
    try {
      await signInWithGoogle();
      // Supabase redirects the browser for OAuth — nothing else to do here.
    } catch (err) {
      setError(err.message || "Couldn't start Google sign-in.");
    }
  };

  return (
    <div className="grid min-h-screen bg-page lg:grid-cols-2">
      <ShowcasePanel />

      <div className="flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-sm">
          <h1 className="font-[var(--font-display)] text-xl font-semibold text-soil-900">
            {mode === "signup" ? "Create an account" : "Sign in"}
          </h1>
          <p className="mt-1 text-sm text-bark-700">
            {mode === "signup"
              ? "Set up access to the tree plantation assistant."
              : "Welcome back — sign in to continue."}
          </p>

          {error && (
            <div className="mt-4 rounded-lg border border-amber-500/40 bg-warning-subtle px-3 py-2.5">
              <p className="text-sm text-warning">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-4 space-y-3">
            <div>
              <label htmlFor="email" className="mb-1 block text-xs font-medium text-bark-700">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-bark-500/25 bg-page px-3 py-2 text-sm text-soil-900 focus:border-leaf-600 focus:outline-none focus:ring-1 focus:ring-leaf-600"
              />
            </div>
            <div>
              <label htmlFor="password" className="mb-1 block text-xs font-medium text-bark-700">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-bark-500/25 bg-page px-3 py-2 text-sm text-soil-900 focus:border-leaf-600 focus:outline-none focus:ring-1 focus:ring-leaf-600"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-lg bg-leaf-700 px-4 py-2.5 text-sm font-medium text-parchment-50 transition hover:bg-leaf-600 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting ? "Please wait…" : mode === "signup" ? "Create account" : "Sign in"}
            </button>
          </form>

          <div className="my-4 flex items-center gap-2">
            <div className="h-px flex-1 bg-bark-500/15" />
            <span className="text-xs text-bark-500">or</span>
            <div className="h-px flex-1 bg-bark-500/15" />
          </div>

          <button
            type="button"
            onClick={handleGoogle}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-bark-500/25 bg-page px-4 py-2.5 text-sm font-medium text-soil-900 transition hover:bg-bark-500/10"
          >
            <svg viewBox="0 0 24 24" className="h-4 w-4">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" />
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.99.66-2.25 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.85A11 11 0 0 0 12 23z" />
              <path fill="#FBBC05" d="M5.84 14.09A6.6 6.6 0 0 1 5.5 12c0-.73.13-1.43.34-2.09V7.06H2.18A11 11 0 0 0 1 12c0 1.78.43 3.46 1.18 4.94z" />
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1A11 11 0 0 0 2.18 7.06l3.66 2.85C6.71 7.31 9.14 5.38 12 5.38z" />
            </svg>
            Continue with Google
          </button>

          <button
            type="button"
            onClick={() => setMode((m) => (m === "signup" ? "signin" : "signup"))}
            className="mt-4 w-full text-center text-sm text-bark-700 underline decoration-leaf-600/40 underline-offset-2 hover:decoration-leaf-600"
          >
            {mode === "signup" ? "Already have an account? Sign in" : "New here? Create an account"}
          </button>
        </div>
      </div>
    </div>
  );
}