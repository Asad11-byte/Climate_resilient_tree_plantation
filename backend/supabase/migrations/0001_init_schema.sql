-- Migration 0001: initial schema
-- Master prompt section 21 lists the full relational schema. Phase 4 only
-- wires up application code (repositories/API) for `tree_species` and
-- `environmental_data`. The remaining tables (documents, document_chunks,
-- locations, chat_sessions, chat_messages, feedback, users) are created here
-- so the schema is complete and future phases don't need another migration
-- just to add a table shape, but no repository/route uses them yet.

-- ============================================================
-- Phase 4 tables (used starting this phase)
-- ============================================================

create table if not exists tree_species (
    id uuid primary key default gen_random_uuid(),
    common_name text not null,
    scientific_name text not null,
    local_names text[],
    soil_requirements text,                 -- null = "Not available in current evidence"
    water_requirement text,
    drought_tolerance text,                 -- e.g. 'low' | 'moderate' | 'high' | null
    heat_tolerance text,
    flood_tolerance text,
    growth_rate text,
    planting_season text,
    plantation_use text,
    local_presence text,                    -- e.g. 'confirmed_mandi_bahauddin' | 'regional' | null
    description text,
    source_ids text[],                      -- references to documents/citations backing these claims
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

comment on table tree_species is
    'Structured species data. Never populate a field with an invented value — '
    'leave it null (surfaced to the API/UI as "Not available in current evidence") '
    'if the source documents do not state it.';

create table if not exists environmental_data (
    id uuid primary key default gen_random_uuid(),
    latitude double precision not null,
    longitude double precision not null,
    soil_ph numeric,
    clay numeric,
    sand numeric,
    organic_carbon numeric,
    temperature numeric,
    rainfall numeric,
    ndvi numeric,
    ndwi numeric,
    land_cover text,
    data_source text not null,              -- e.g. 'SoilGrids', 'NASA POWER' — never blank
    retrieved_at timestamptz not null default now()
);

comment on table environmental_data is
    'Modelled/estimated environmental properties per coordinate, cached from '
    'external datasets (Phase 5). Always modelled estimates, not field '
    'measurements, unless data_source explicitly says otherwise — the API '
    'must phrase these as "Estimated ... from [data_source]".';

create index if not exists idx_environmental_data_lat_lon
    on environmental_data (latitude, longitude);

-- ============================================================
-- Scaffolded for later phases (schema only, no app code yet)
-- ============================================================

create table if not exists documents (
    id uuid primary key default gen_random_uuid(),
    title text not null,
    source text not null,
    source_url text,
    location text,
    province text,
    country text,
    year int,
    document_type text,
    topic text,
    file_type text,
    content_hash text unique,               -- matches RawDocument.document_id from ingestion
    created_at timestamptz not null default now()
);

create table if not exists document_chunks (
    id uuid primary key default gen_random_uuid(),
    document_id uuid references documents(id) on delete cascade,
    chunk_index int not null,
    page int,
    breadcrumb text,
    qdrant_point_id text,                   -- links back to the Qdrant vector point
    created_at timestamptz not null default now(),
    unique (document_id, chunk_index)
);

create table if not exists locations (
    id uuid primary key default gen_random_uuid(),
    name text,
    latitude double precision not null,
    longitude double precision not null,
    created_at timestamptz not null default now()
);

create table if not exists chat_sessions (
    id uuid primary key default gen_random_uuid(),
    user_id uuid,
    created_at timestamptz not null default now()
);

create table if not exists chat_messages (
    id uuid primary key default gen_random_uuid(),
    session_id uuid references chat_sessions(id) on delete cascade,
    role text not null,                     -- 'user' | 'assistant'
    content text not null,
    query_category text,
    evidence_available boolean,
    sources jsonb,
    created_at timestamptz not null default now()
);

create table if not exists feedback (
    id uuid primary key default gen_random_uuid(),
    chat_message_id uuid references chat_messages(id) on delete set null,
    rating int,                             -- e.g. 1-5 or thumbs up/down as 1/0
    comment text,
    created_at timestamptz not null default now()
);
