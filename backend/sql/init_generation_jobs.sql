create table if not exists generation_jobs (
    job_id text primary key,
    comfyui_prompt_id text,
    status text not null,
    error_message text,
    prompt text not null,
    negative_prompt text,
    width integer not null,
    height integer not null,
    steps integer not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);