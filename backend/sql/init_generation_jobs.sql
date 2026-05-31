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
    result_image_data_url text,
    result_mime_type text,
    completed_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);