-- 0002_auth_user_scoping.sql
--
-- Wires chat_sessions to Supabase Auth (auth.users is now the single
-- source of identity — the placeholder public.users table is dropped
-- rather than duplicated) and adds RLS as defense-in-depth.
--
-- IMPORTANT — destructive step: this deletes any chat_sessions rows that
-- have no user_id (i.e. anything created before auth existed). Under the
-- new required-auth model those rows can never be listed or reached by
-- any user again anyway, and user_id is being set NOT NULL below. Back up
-- first if you want to keep that data for any reason.

drop table if exists public.users;

delete from chat_sessions where user_id is null;

alter table chat_sessions
  alter column user_id set not null,
  add constraint chat_sessions_user_id_fkey
    foreign key (user_id) references auth.users(id) on delete cascade;

alter table chat_sessions enable row level security;
alter table chat_messages enable row level security;

-- Defense-in-depth only. The backend connects with the service_role key
-- (bypasses RLS) and enforces user_id scoping explicitly in
-- ChatSessionRepository / ChatMessageRepository — these policies matter
-- only if these tables are ever queried directly with the anon key.

create policy "select own sessions" on chat_sessions
  for select using (user_id = auth.uid());

create policy "insert own sessions" on chat_sessions
  for insert with check (user_id = auth.uid());

create policy "update own sessions" on chat_sessions
  for update using (user_id = auth.uid()) with check (user_id = auth.uid());

create policy "delete own sessions" on chat_sessions
  for delete using (user_id = auth.uid());

create policy "select own messages" on chat_messages
  for select using (
    exists (
      select 1 from chat_sessions
      where chat_sessions.id = chat_messages.session_id
        and chat_sessions.user_id = auth.uid()
    )
  );

create policy "insert own messages" on chat_messages
  for insert with check (
    exists (
      select 1 from chat_sessions
      where chat_sessions.id = chat_messages.session_id
        and chat_sessions.user_id = auth.uid()
    )
  );