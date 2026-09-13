import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL;
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  // Fail loudly at boot rather than let every auth call fail mysteriously.
  throw new Error(
    "VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY must be set. " +
      "Use the anon/public key here — never the service_role key or the JWT secret; " +
      "both of those belong only in the backend's .env, never in a VITE_-prefixed variable."
  );
}

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);