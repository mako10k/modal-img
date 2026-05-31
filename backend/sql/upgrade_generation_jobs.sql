begin;

do $$
begin
    if exists (
        select 1
        from information_schema.columns
        where table_name = 'generation_jobs'
          and column_name = 'workflow_id'
    ) and not exists (
        select 1
        from information_schema.columns
        where table_name = 'generation_jobs'
          and column_name = 'comfyui_prompt_id'
    ) then
        alter table generation_jobs rename column workflow_id to comfyui_prompt_id;
    end if;
end $$;

alter table generation_jobs
    add column if not exists comfyui_prompt_id text,
    add column if not exists error_message text,
    add column if not exists created_at timestamptz not null default now(),
    add column if not exists updated_at timestamptz not null default now();

alter table generation_jobs
    alter column comfyui_prompt_id drop not null;

update generation_jobs
set status = 'queued'
where status = 'accepted';

commit;