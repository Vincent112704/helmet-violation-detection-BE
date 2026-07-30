-- ============================================================================
-- dashboard_metrics(days_back)
--
-- Returns every dashboard metric as a single JSON object shaped to match
-- app.models.responses.MetricResponse, so the repository can hand the result
-- straight to Pydantic without any server-side aggregation.
--
-- Install once against the database (SQL Editor / migration), then call from
-- the repository with:
--     supabase.rpc("dashboard_metrics", {"days_back": 30}).execute()
--
-- Scope of days_back: it bounds the TREND series only. The KPI cards and the
-- pie chart are all-time totals ("Total Violations" is inherently all-time),
-- and the location histogram covers all data so hotspots reflect full history.
--
-- All date boundaries are evaluated in Asia/Manila, not UTC. The `timestamp`
-- column is assumed to be timestamptz stored as UTC; a naive ::date cast would
-- misfile every violation recorded after 4:00 PM UTC into the following day.
--
-- Assumes table public.tickets (ticket_id, officer, status, plate_number,
-- location, timestamp, url) per app/models/tickets.py.
-- ============================================================================

create or replace function public.dashboard_metrics(days_back integer default 30)
returns json
language sql
stable
as $$
with bounds as (
    select
        -- Start of "today" in Manila, expressed as an absolute instant so all
        -- comparisons below stay sargable against an index on "timestamp".
        (((now() at time zone 'Asia/Manila')::date)::timestamp
            at time zone 'Asia/Manila')                          as today_start,
        -- First day of the trend window (inclusive).
        ((
            ((now() at time zone 'Asia/Manila')::date - (days_back - 1))::timestamp)
            at time zone 'Asia/Manila')                          as window_start,
        (now() at time zone 'Asia/Manila')::date                 as today_local
),

-- ---------------------------------------------------------------------------
-- All four KPI cards from a single pass over the table.
-- ---------------------------------------------------------------------------
kpis as (
    select
        count(*) filter (where t.status != 'false_alarm')    as total_violations,
        count(*) filter (where t.status = 'issued')     as tickets_issued,
        count(*) filter (where t.status = 'pending')    as tickets_pending,
        count(*) filter (where t.status = 'false_alarm') as tickets_appealed,
        count(*) filter (
            where t."timestamp" >= b.today_start
              and t."timestamp" <  b.today_start + interval '1 day'
        )                                               as violations_today
    from public.ticket t
    cross join bounds b
),

-- ---------------------------------------------------------------------------
-- Pie chart. Every TicketStatus is emitted even at zero, so the chart keeps a
-- stable set of slices instead of dropping a category on an empty day.
-- ---------------------------------------------------------------------------
status_totals as (
    select t.status::text as status, count(*) as violations
    from public.ticket t
    group by 1
),
pie_chart as (
    select json_object_agg(s.status, coalesce(c.violations, 0)) as obj
    from (values ('pending'), ('issued'), ('false_alarm')) as s(status)
    left join status_totals c on c.status = s.status
),

-- ---------------------------------------------------------------------------
-- Trend. generate_series supplies the full calendar so days with no violations
-- appear as explicit zeroes; a bare GROUP BY would omit them and the chart
-- would interpolate a straight line across the gap.
-- ---------------------------------------------------------------------------
trend_days as (
    select generate_series(
        (select today_local from bounds) - (days_back - 1),
        (select today_local from bounds),
        interval '1 day'
    )::date as happen
),
trend_counts as (
    select
        (t."timestamp" at time zone 'Asia/Manila')::date as happen,
        count(*)                                         as violations
    from public.ticket t
    cross join bounds b
    where t."timestamp" >= b.window_start
    group by 1
),
trend as (
    select json_agg(
               json_build_object(
                   'happen',     d.happen,
                   'violations', coalesce(c.violations, 0)
               )
               order by d.happen
           ) as arr
    from trend_days d
    left join trend_counts c using (happen)
),

-- ---------------------------------------------------------------------------
-- Location histogram, busiest first.
-- ---------------------------------------------------------------------------
location_analysis as (
    select json_agg(
               json_build_object(
                   'location',   l.location,
                   'violations', l.violations
               )
               order by l.violations desc, l.location
           ) as arr
    from (
        select t.location, count(*) as violations
        from public.ticket t
        group by t.location
    ) l
)

select json_build_object(
    'pie_chart',         coalesce((select obj from pie_chart), '{}'::json),
    'violations_today',  (select violations_today from kpis),
    'total_violations',  (select total_violations from kpis),
    'tickets_issued',    (select tickets_issued   from kpis),
    'tickets_pending',   (select tickets_pending  from kpis),
    'tickets_appealed',  (select tickets_appealed  from kpis),
    -- coalesce guards the empty-table case: json_agg returns NULL, not '[]',
    -- and NULL would fail Pydantic validation on a non-optional list field.
    'trend_analysis',    coalesce((select arr from trend),             '[]'::json),
    'location_analysis', coalesce((select arr from location_analysis), '[]'::json)
);
$$;

-- PostgREST exposes this to the anon/authenticated roles only once granted.
-- Drop `anon` if the dashboard is behind auth, which it should be.
grant execute on function public.dashboard_metrics(integer) to authenticated;

-- ============================================================================
-- Notes
-- ============================================================================
--
-- Row-level security: this function runs SECURITY INVOKER (the default), so
-- RLS on public.tickets still applies and an officer sees only the rows they
-- are allowed to see. If the dashboard must show force-wide totals regardless
-- of who is asking, recreate it as:
--
--     ... language sql stable security definer set search_path = public, pg_temp
--
-- The `set search_path` is not optional there: without it a SECURITY DEFINER
-- function is a privilege-escalation vector.
--
-- Supporting indexes -- the query plans above assume these exist. Run once:
--
--     create index if not exists tickets_timestamp_idx on public.tickets ("timestamp" desc);
--     create index if not exists tickets_status_idx    on public.tickets (status);
--     create index if not exists tickets_location_idx  on public.tickets (location);
--
-- For an append-only violations log that grows large, BRIN is a much smaller
-- alternative to the btree on "timestamp":
--
--     create index if not exists tickets_timestamp_brin on public.tickets
--         using brin ("timestamp");
