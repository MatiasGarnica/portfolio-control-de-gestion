-- Esquema aplicado en Supabase (proyecto caso05-cadena-demo), 2026-11-09
-- Caso 05 · Cadena Demo S.A. (datos ficticios). Modelo estrella + seguridad por fila (RLS).
create table public.dim_local (local_id text primary key, local text not null, region text not null, formato text not null, m2 int, apertura text);
create table public.dim_rubro (rubro_id int primary key, rubro text not null, tipo text not null, signo int not null, grupo_puente text not null);
create table public.dim_calendario (periodo text primary key, anio int, mes int, inflacion_mensual_pct numeric, ipc_indice numeric, inflacion_ppto_pct numeric, ipc_ppto_indice numeric);
create table public.fact_resultados (periodo text references public.dim_calendario, local_id text references public.dim_local, rubro_id int references public.dim_rubro, "real" bigint, presupuesto bigint, primary key (periodo, local_id, rubro_id));
create table public.fact_operativo (periodo text references public.dim_calendario, local_id text references public.dim_local, tickets int, ticket_promedio int, dotacion int, horas_trabajadas int, bajas_personal int, tickets_ppto int, ticket_promedio_ppto int, primary key (periodo, local_id));
create table public.fact_nomina (periodo text references public.dim_calendario, local_id text references public.dim_local, puesto text, dotacion int, horas_normales int, horas_extra int, costo_total bigint, primary key (periodo, local_id, puesto));
create table public.fact_incidentes (incidente_id text primary key, fecha date, local_id text references public.dim_local, tipo text, horas_afectadas int, impacto_estimado_ventas bigint, detalle text);
create index on public.fact_resultados (local_id);
create index on public.fact_operativo (local_id);
create index on public.fact_nomina (local_id);
create index on public.fact_incidentes (local_id);

create table public.perfiles (
  user_id uuid primary key references auth.users on delete cascade,
  email text not null,
  rol text not null check (rol in ('Dirección', 'Gerente regional', 'Gerente de local', 'Supervisor')),
  region text,
  local_id text references public.dim_local
);

create schema if not exists app;
create or replace function app.mi_rol() returns text language sql stable security definer set search_path = '' as
  $$ select rol from public.perfiles where user_id = (select auth.uid()) $$;
create or replace function app.mi_region() returns text language sql stable security definer set search_path = '' as
  $$ select region from public.perfiles where user_id = (select auth.uid()) $$;
create or replace function app.mi_local() returns text language sql stable security definer set search_path = '' as
  $$ select local_id from public.perfiles where user_id = (select auth.uid()) $$;
create or replace function app.puede_ver_local(p_local text) returns boolean language sql stable security definer set search_path = '' as $$
  select case app.mi_rol()
    when 'Dirección' then true
    when 'Gerente regional' then exists (select 1 from public.dim_local d where d.local_id = p_local and d.region = app.mi_region())
    when 'Gerente de local' then p_local = app.mi_local()
    else false end
$$;
revoke all on schema app from public;
grant usage on schema app to authenticated;
revoke execute on all functions in schema app from public;
grant execute on all functions in schema app to authenticated;

alter table public.dim_local enable row level security;
alter table public.dim_rubro enable row level security;
alter table public.dim_calendario enable row level security;
alter table public.fact_resultados enable row level security;
alter table public.fact_operativo enable row level security;
alter table public.fact_nomina enable row level security;
alter table public.fact_incidentes enable row level security;
alter table public.perfiles enable row level security;

create policy "dimensiones visibles con login" on public.dim_local for select to authenticated using (true);
create policy "dimensiones visibles con login" on public.dim_rubro for select to authenticated using (true);
create policy "dimensiones visibles con login" on public.dim_calendario for select to authenticated using (true);
create policy "ve sus locales" on public.fact_resultados for select to authenticated using ((select app.puede_ver_local(local_id)));
create policy "ve sus locales" on public.fact_operativo for select to authenticated using ((select app.puede_ver_local(local_id)));
create policy "ve sus locales" on public.fact_nomina for select to authenticated using ((select app.puede_ver_local(local_id)));
create policy "ve incidentes de sus locales" on public.fact_incidentes for select to authenticated
  using ((select app.puede_ver_local(local_id)) or ((select app.mi_rol()) = 'Supervisor' and local_id = (select app.mi_local())));
create policy "ve su propio perfil" on public.perfiles for select to authenticated using (user_id = (select auth.uid()));

create or replace function public.promedio_red()
returns table (periodo text, rubro_id int, monto_real numeric, monto_ppto numeric, locales int)
language sql stable security definer set search_path = '' as $$
  select r.periodo, r.rubro_id, sum(r."real")::numeric, sum(r.presupuesto)::numeric, count(distinct r.local_id)::int
  from public.fact_resultados r
  where (select app.mi_rol()) is not null
  group by r.periodo, r.rubro_id
$$;
create or replace function public.promedio_formato()
returns table (formato text, periodo text, rubro_id int, monto_real numeric, monto_ppto numeric, locales int)
language sql stable security definer set search_path = '' as $$
  select d.formato, r.periodo, r.rubro_id, sum(r."real")::numeric, sum(r.presupuesto)::numeric, count(distinct r.local_id)::int
  from public.fact_resultados r join public.dim_local d using (local_id)
  where (select app.mi_rol()) is not null
  group by d.formato, r.periodo, r.rubro_id
  having count(distinct r.local_id) >= 3
$$;
revoke execute on function public.promedio_red() from public, anon;
revoke execute on function public.promedio_formato() from public, anon;
grant execute on function public.promedio_red() to authenticated;
grant execute on function public.promedio_formato() to authenticated;
