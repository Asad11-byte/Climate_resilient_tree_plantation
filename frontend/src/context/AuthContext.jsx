import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { supabase } from "../api/supabaseClient";

const AuthContext = createContext(null);

/**
 * Where Supabase should send the user back to after an email-confirmation
 * link or an OAuth redirect. Built from window.location.origin rather than
 * a hardcoded/env value — that resolves to http://localhost:5173 in dev and
 * the real Vercel domain in production automatically, with no separate
 * config needed per environment.
 *
 * This still has to appear on Supabase's Redirect URLs allow-list
 * (Authentication -> URL Configuration) — passing redirectTo only tells
 * Supabase which allowed URL to use, it doesn't add one to the allow-list.
 */
function getRedirectUrl() {
  return `${window.location.origin}/assistant`;
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });

    const { data: listener } = supabase.auth.onAuthStateChange((_event, newSession) => {
      setSession(newSession);
    });

    return () => listener.subscription.unsubscribe();
  }, []);

  const signInWithPassword = useCallback(async (email, password) => {
    // No redirect involved here — password sign-in returns a session
    // directly, there's no email link or OAuth hop to send back correctly.
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
  }, []);

  const signUp = useCallback(async (email, password) => {
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: { emailRedirectTo: getRedirectUrl() },
    });
    if (error) throw error;
  }, []);

  const signInWithGoogle = useCallback(async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: getRedirectUrl() },
    });
    if (error) throw error;
  }, []);

  const signOut = useCallback(async () => {
    await supabase.auth.signOut();
  }, []);

  const value = {
    session,
    user: session?.user ?? null,
    loading,
    signInWithPassword,
    signUp,
    signInWithGoogle,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}