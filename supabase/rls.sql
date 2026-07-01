-- BudgetMe Row Level Security for Supabase Realtime (Django users).
-- Run once in Supabase → SQL Editor after migrations exist.
-- Requires Django JWT with claim: django_user_id = auth_user.id

create or replace function public.current_django_user_id()
returns bigint
language sql
stable
as $$
  select nullif(auth.jwt() ->> 'django_user_id', '')::bigint;
$$;

-- budgetbuddy_budgetprofile
alter table public.budgetbuddy_budgetprofile enable row level security;
drop policy if exists "profile_select_own" on public.budgetbuddy_budgetprofile;
create policy "profile_select_own" on public.budgetbuddy_budgetprofile
for select to authenticated using (user_id = public.current_django_user_id());

-- Child tables (profile_id ownership)
-- Repeat pattern for: budgetcategory, expense, transaction, mobilemoneytransaction, savingsdeposit

alter table public.budgetbuddy_transaction enable row level security;
drop policy if exists "transaction_select_own" on public.budgetbuddy_transaction;
create policy "transaction_select_own" on public.budgetbuddy_transaction
for select to authenticated using (
  profile_id in (
    select id from public.budgetbuddy_budgetprofile
    where user_id = public.current_django_user_id()
  )
);

alter table public.budgetbuddy_mobilemoneytransaction enable row level security;
drop policy if exists "mm_select_own" on public.budgetbuddy_mobilemoneytransaction;
create policy "mm_select_own" on public.budgetbuddy_mobilemoneytransaction
for select to authenticated using (
  profile_id in (
    select id from public.budgetbuddy_budgetprofile
    where user_id = public.current_django_user_id()
  )
);

alter table public.budgetbuddy_savingsdeposit enable row level security;
drop policy if exists "savings_select_own" on public.budgetbuddy_savingsdeposit;
create policy "savings_select_own" on public.budgetbuddy_savingsdeposit
for select to authenticated using (
  profile_id in (
    select id from public.budgetbuddy_budgetprofile
    where user_id = public.current_django_user_id()
  )
);

-- Realtime publication
alter publication supabase_realtime add table public.budgetbuddy_transaction;
alter publication supabase_realtime add table public.budgetbuddy_mobilemoneytransaction;
alter publication supabase_realtime add table public.budgetbuddy_savingsdeposit;

alter table public.budgetbuddy_transaction replica identity full;
alter table public.budgetbuddy_mobilemoneytransaction replica identity full;
alter table public.budgetbuddy_savingsdeposit replica identity full;
