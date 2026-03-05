# Core

## Purpose

The core subsystem provides the foundational runtime for ragling: configuration
loading, database management, document conversion caching, embedding
generation, indexing orchestration, leader election, and the MCP server that
exposes all capabilities as tools.

The key design decision is single-writer architecture: all database writes flow
through one IndexingQueue worker thread per group, eliminating write contention
by design. Reads (search, listing) happen on separate connections using WAL mode
for concurrent access across multiple MCP instances.

## Core Mechanism

Configuration is frozen and immutable to prevent race conditions across threads.
All writes flow through the IndexingQueue's single worker thread; reads use
separate WAL-mode connections. Leader election via `fcntl.flock()` delegates to
the kernel for automatic cleanup on process death.

**Key files:**
- `config.py` -- frozen Config dataclass and `load_config()`
- `db.py` -- connection management, schema, migrations
- `doc_store.py` -- content-addressed conversion cache
- `embeddings.py` -- Ollama embedding interface
- `indexing_queue.py` -- single-writer job queue
- `indexing_status.py` -- thread-safe progress tracking
- `leader.py` -- per-group leader election via flock
- `sync.py` -- startup discovery and file routing
- `mcp_server.py` -- thin facade: auth setup, `ToolContext` creation, `create_server()`, re-exports for backward compat
- `tools/` -- MCP tool package; each tool in its own module with `register(mcp, ctx)` pattern
- `tools/context.py` -- `ToolContext` dataclass replacing closure captures (group_name, server_config, indexing_status, config_getter, queue_getter, role_getter)
- `tools/helpers.py` -- shared helpers: `_build_source_uri`, `_result_to_dict`, `_get_user_context`, `_convert_document`, etc.
- `tools/{search,batch_search,list_collections,collection_info,index,indexing_status,doc_store_info,search_task,convert}.py` -- one tool per module
- `server.py` -- `ServerOrchestrator` class: startup orchestration (leader election, queue management, config watching, watcher startup, shutdown)
- `cli.py` -- Click CLI commands; `serve` delegates to `ServerOrchestrator`
- `path_mapping.py` -- host/container path translation
- `query_logger.py` -- JSONL query logging
- `indexer_types.py` -- IndexerType enum

## Public Interface

| Export | Used By | Contract |
|---|---|---|
| `Config`, `load_config()` | All subsystems | Frozen dataclass; `with_overrides()` returns new instance |
| `get_connection()`, `init_db()` | Indexers, search, CLI | Returns sqlite3.Connection with sqlite-vec loaded, WAL mode, busy_timeout set |
| `get_or_create_collection()`, `delete_collection()` | Indexers, IndexingQueue | Collection CRUD; `get_or_create_collection()` returns collection_id, `delete_collection()` removes collection and cascaded rows |
| `DocStore` | Indexers (via IndexingQueue) | Content-addressed cache; `get_or_convert(path, converter, config_hash)` |
| `get_embedding()`, `get_embeddings()`, `serialize_float32()` | Indexers, search | Ollama embedding with retry; binary serialization for sqlite-vec |
| `OllamaConnectionError` | MCP server, CLI | Raised when Ollama is unreachable |
| `IndexingQueue`, `IndexJob` | CLI (serve), sync, watcher | Single-writer queue; `submit()`, `submit_and_wait()`, `shutdown()` |
| `IndexingStatus` | IndexingQueue, MCP server | Thread-safe progress; `to_dict()` returns status or None when idle |
| `LeaderLock`, `lock_path_for_config()` | ServerOrchestrator | `try_acquire()` returns bool; kernel releases on process death |
| `ServerOrchestrator` | CLI (serve) | Startup orchestration; `run()` manages leader election, queue, watchers, shutdown |
| `create_server()` | ServerOrchestrator | Returns configured FastMCP instance |
| `run_startup_sync()`, `submit_file_change()`, `map_file_to_collection()` | ServerOrchestrator, watcher | Daemon thread discovery; file-to-collection routing |
| `apply_forward()`, `apply_reverse()`, `apply_forward_uri()` | MCP server | Longest-prefix path translation between host and container |
| `log_query()` | MCP server | JSONL append with fsync |
| `IndexerType` | IndexingQueue, sync, CLI | StrEnum: PROJECT, CODE, OBSIDIAN, EMAIL, CALIBRE, RSS, PRUNE |

## Invariants

| ID | Invariant | Why It Matters |
|---|---|---|
| INV-1 | Config is a frozen dataclass; mutation raises `FrozenInstanceError` | Shared across threads; mutation would cause race conditions |
| INV-2 | `load_config()` never raises on malformed input; returns default Config | Server must start even with broken config file |
| INV-3 | All SQLite databases use WAL journal mode with retry on first access | Multiple MCP instances read concurrently; WAL avoids reader/writer blocking |
| INV-4 | Only the IndexingQueue worker thread writes to the per-group index database. The MCP `rag_index` tool (in `tools/index.py`) requires a running queue; direct indexing has been removed. | Eliminates write contention; no locking needed in indexers |
| INV-5 | DocStore keys documents by SHA-256 file hash + config_hash; identical content is never converted twice | Avoids redundant Docling conversions that can take minutes per document |
| INV-8 | LeaderLock uses `fcntl.flock()`; kernel releases the lock when the process dies | No stale locks, no PID files, no heartbeat mechanism needed |
| INV-9 | Embedding batch failures fall back to individual embedding with truncation retry | One bad text in a batch must not block the entire batch |

## Failure Modes

| ID | Symptom | Cause | Fix |
|---|---|---|---|
| FAIL-1 | `OllamaConnectionError` on search or index | Ollama not running or unreachable at configured host | Start Ollama with `ollama serve`; verify `ollama_host` config if using remote |
| FAIL-2 | `OperationalError: database is locked` during WAL setup | Concurrent first-time access to a new database file | Automatic retry with exponential backoff (5 attempts); increase delay if persistent |
| FAIL-4 | IndexingQueue silently drops errors | Indexer raises during `_process()` | Exception logged; status counter decremented; job marked failed in IndexingStatus |
| FAIL-5 | Follower never promoted to leader | Previous leader process died but OS did not release flock | Restart the follower; kernel should release on process death -- if not, check for zombie processes |

## Dependencies

| Dependency | Type | SPEC.md Path |
|---|---|---|
| Document | internal | `src/ragling/document/SPEC.md` -- document conversion, chunking, format bridging |
| Auth | internal | `src/ragling/auth/SPEC.md` -- API key resolution, TLS, token verification |
| Search | internal | `src/ragling/search/SPEC.md` -- hybrid search with RRF |
| Watchers | internal | `src/ragling/watchers/SPEC.md` -- filesystem, database, config change monitoring |
| Indexers | internal (circular) | `src/ragling/indexers/SPEC.md` -- Core dispatches to indexers via IndexingQueue; indexers depend on Core utilities. Mutual dependency by design. |
| sqlite-vec | external | N/A -- SQLite extension for vector similarity search |
| Ollama | external | N/A -- local LLM/embedding server |
| FastMCP | external | N/A -- MCP server framework |
| Click | external | N/A -- CLI framework |
---
# Auth

## Purpose

API key resolution, TLS certificate management, and rate-limited token
verification for the MCP server transport layer.

## Core Mechanism

API key comparison uses `hmac.compare_digest` for timing-safety. Rate limiting
uses exponential backoff to prevent brute-force attempts without permanently
locking out users. TLS certificates are self-signed ECDSA P-256 with
auto-renewal.

**Key files:**
- `auth.py` -- API key resolution and user context
- `tls.py` -- self-signed certificate generation
- `token_verifier.py` -- rate-limited token verification

## Public Interface

| Export | Used By | Contract |
|---|---|---|
| `resolve_api_key(key, config)` | MCP server | Timing-safe key lookup; returns `UserContext` or `None` |
| `UserContext` | MCP server | Dataclass with username; `visible_collections()` computes access |
| `RaglingTokenVerifier` | MCP server | Rate-limited token verification with exponential backoff |
| `RateLimitedError` | MCP server | Raised when client exceeds failure threshold |
| `ensure_tls_certs(tls_dir?)` | CLI (serve) | Returns `TLSConfig` with (cert_path, key_path, ca_path); auto-renews on expiry |

## Invariants

| ID | Invariant | Why It Matters |
|---|---|---|
| INV-7 | `resolve_api_key()` uses `hmac.compare_digest` for all key comparisons | Prevents timing side-channel attacks on API keys |
| INV-12 | Token verifier rate-limits failed auth attempts with exponential backoff capped at 300 seconds | Prevents brute-force API key guessing without permanently locking out users |

## Failure Modes

| ID | Symptom | Cause | Fix |
|---|---|---|---|
| FAIL-7 | Rate limiter blocks legitimate user after failed attempts | More than MAX_FAILURES (5) consecutive failures with wrong key (triggers on 6th attempt, `count > 5`) | Wait for backoff to expire (max 300s); or restart the server to clear rate-limit state |

## Dependencies

| Dependency | Type | SPEC.md Path |
|---|---|---|
| `config.py` (Config) | internal | `src/ragling/SPEC.md` |
| cryptography | external | N/A -- X.509 certificate generation |
---
# Document

## Purpose

Document conversion, chunking, and format bridging for the indexing pipeline.
All external formats (PDF, DOCX, PPTX, XLSX, HTML, images, audio, markdown,
EPUB, plaintext, email, RSS) are normalised into `Chunk` objects via either
Docling's `HybridChunker` or word-based window splitting.

## Core Mechanism

All external formats are normalized into `Chunk` objects via Docling's
`HybridChunker` or word-based window splitting. Formats not natively supported
by Docling are bridged into `DoclingDocument` objects so every format flows
through the same chunking pipeline.

**Key files:**
- `chunker.py` -- Chunk dataclass and window splitting
- `docling_convert.py` -- Docling conversion, HybridChunker, VLM fallbacks
- `docling_bridge.py` -- legacy parser output to DoclingDocument bridge
- `audio_metadata.py` -- audio/video container metadata extraction via mutagen

## Public Interface

| Export | Used By | Contract |
|---|---|---|
| `Chunk` | Indexers, parsers | Dataclass with text, title, metadata, chunk_index |
| `split_into_windows(text, size, overlap)` | Parsers (spec.py) | Returns `list[Chunk]` of overlapping word windows |
| `word_count(text)` | Parsers (spec.py) | Returns integer word count |
| `convert_and_chunk(path, doc_store, config, ...)` | Indexers (Obsidian, Project, Calibre) | Docling conversion with DocStore caching + HybridChunker; returns `list[Chunk]` |
| `chunk_with_hybrid(doc, ...)` | Indexers, `convert_and_chunk()` | Chunks a DoclingDocument via HybridChunker with `contextualize()`; returns `list[Chunk]` |
| `converter_config_hash(config)` | Indexers | Deterministic hash of pipeline settings for DocStore cache keying |
| `DOCLING_FORMATS` | Indexers, MCP server | Frozenset of file extensions supported by Docling |
| `markdown_to_docling_doc(text, title)` | Indexers (Obsidian, Project) | Bridge: markdown text to DoclingDocument |
| `epub_to_docling_doc(chapters, title)` | Indexers (Obsidian, Project) | Bridge: EPUB chapters to DoclingDocument |
| `plaintext_to_docling_doc(text, title)` | Indexers (Project) | Bridge: plain text to DoclingDocument |
| `email_to_docling_doc(subject, body)` | Indexers (Email) | Bridge: email content to DoclingDocument |
| `rss_to_docling_doc(title, body)` | Indexers (RSS) | Bridge: RSS article to DoclingDocument |
| `extract_audio_metadata(path)` | Indexers (Obsidian, Project) | Returns dict of audio/video metadata or empty dict on failure |

## Invariants

| ID | Invariant | Why It Matters |
|---|---|---|
| INV-1 | Docling `DocumentConverter` is a process-wide singleton via `lru_cache` on `get_converter()` | Creating multiple converters wastes memory and initialization time; singleton ensures consistent pipeline settings |
| INV-2 | `convert_and_chunk()` requires a `DocStore` for Docling-handled formats | Content-addressed caching prevents redundant conversions; callers must provide a DocStore or get an error log and empty result |
| INV-3 | `split_into_windows()` returns non-empty output for non-empty input | Downstream code assumes at least one chunk per non-empty text; empty output would produce sources with zero documents |
| INV-4 | Audio metadata extraction is best-effort — failures return empty dict, never raise | One corrupt audio file must not abort an indexing batch |

## Failure Modes

| ID | Symptom | Cause | Fix |
|---|---|---|---|
| FAIL-1 | `convert_and_chunk()` returns chunks from pypdfium2 text instead of Docling | Primary Docling conversion failed (corrupted PDF, missing fonts) | Automatic fallback; quality may be reduced — re-index if the source file is fixed |
| FAIL-2 | `ValueError` raised from `convert_and_chunk()` | Unsupported `source_type` passed (not in `DOCLING_FORMATS`) | Programming error in caller — check `DOCLING_FORMATS` before calling |
| FAIL-3 | `extract_audio_metadata()` returns empty dict | Corrupt or unsupported audio container | File is logged and skipped; metadata fields will be empty in search results |

## Dependencies

| Dependency | Type | SPEC.md Path |
|---|---|---|
| `config.py` (Config) | internal | `src/ragling/SPEC.md` |
| `doc_store.py` (DocStore) | internal | `src/ragling/SPEC.md` |
| Docling | external | N/A -- document conversion (PDF, DOCX, etc.) |
| mutagen | external | N/A -- audio/video metadata extraction |
---
# Indexers

## Purpose

Source-specific indexing pipelines that discover content, detect changes,
parse via the parsers subsystem, chunk and embed text, and persist results
to the per-group SQLite database. Every indexer extends `BaseIndexer` ABC
and implements the `index()` method.

The key design decision: two-pass indexing (scan for changes, then index
changed sources) combined with three change-detection strategies -- file
hash, watermark timestamp, and HEAD SHA comparison -- to keep incremental
re-indexing fast across heterogeneous source types.

## Core Mechanism

Two-pass indexing (scan for changes, then index changed sources) with three
change-detection strategies: file hash, watermark timestamp, and HEAD SHA
comparison. `ProjectIndexer` auto-discovers nested vaults and git repos,
delegates to specialized indexers, and excludes repos already covered by
explicit `code_groups`.

**Key files:**
- `base.py` -- `BaseIndexer` ABC, `upsert_source_with_chunks()`,
  `delete_source()`, `prune_stale_sources()`, `IndexResult`, `file_hash()`
- `auto_indexer.py` -- `detect_directory_type()`,
  `detect_indexer_type_for_file()`, `collect_indexable_directories()`
- `discovery.py` -- `discover_sources()`, `reconcile_sub_collections()`,
  `DiscoveredSource`, `DiscoveryResult`
- `obsidian.py` -- `ObsidianIndexer` for Obsidian vault files
- `email_indexer.py` -- `EmailIndexer` for eM Client emails
- `calibre_indexer.py` -- `CalibreIndexer` for Calibre ebooks
- `git_commands.py` -- pure git subprocess helpers: `run_git()`,
  `is_git_repo()`, `get_head_sha()`, `git_ls_files()`, `CommitInfo`,
  `FileChange`, and commit history/diff extraction functions
- `git_indexer.py` -- `GitRepoIndexer` for code repos (tree-sitter +
  commit history); delegates git CLI operations to `git_commands.py`
- `rss_indexer.py` -- `RSSIndexer` for NetNewsWire RSS articles
- `factory.py` -- `create_indexer()` centralized indexer creation; single
  source of truth for mapping collection names/types to indexer instances
- `format_routing.py` -- `EXTENSION_MAP`, `SUPPORTED_EXTENSIONS`,
  `is_supported_extension()`, `parse_and_chunk()` shared format dispatch
- `project.py` -- `ProjectIndexer` with auto-discovery and delegation;
  re-exports `_EXTENSION_MAP`, `_SUPPORTED_EXTENSIONS` for backward compat

## Public Interface

| Export | Used By | Contract |
|---|---|---|
| `create_indexer()` | `indexing_queue.py`, `cli.py` | Factory function: maps collection name/IndexerType to configured indexer instance |
| `BaseIndexer` ABC | All indexers | Must implement `index(conn, config, force, status) -> IndexResult` |
| `upsert_source_with_chunks()` | All indexers | Atomic delete-then-insert of source + documents + vectors; commits transaction |
| `delete_source()` | `GitRepoIndexer`, `prune_stale_sources()` | Removes source row and cascaded documents/vectors; no-op if source absent |
| `prune_stale_sources()` | `ObsidianIndexer`, `CalibreIndexer`, `ProjectIndexer` | Removes file-backed sources whose files no longer exist; skips virtual URIs |
| `file_hash()` | All file-based indexers | Returns SHA-256 hex digest of file contents |
| `IndexResult` | All indexers, `indexing_queue.py` | Dataclass tracking indexed/skipped/skipped_empty/pruned/errors/total_found counts plus `error_messages: list[str]` |
| `detect_directory_type()` | `ProjectIndexer`, sync module | Returns `IndexerType.OBSIDIAN`, `CODE`, or `PROJECT` based on marker files |
| `detect_indexer_type_for_file()` | Sync module | Walks parent directories for `.obsidian`/`.git` markers; returns `IndexerType` |
| `collect_indexable_directories()` | Sync module | Filters configured usernames against existing subdirectories |
| `discover_sources()` | `ProjectIndexer` | Recursively scans for `.obsidian`/`.git` markers; returns `DiscoveryResult` |
| `reconcile_sub_collections()` | `ProjectIndexer` | Deletes sub-collections whose markers no longer exist |
| `ObsidianIndexer` | `indexing_queue.py`, `ProjectIndexer` | Indexes all supported file types in Obsidian vaults |
| `EmailIndexer` | `indexing_queue.py` | Indexes emails from eM Client with watermark-based incrementality |
| `CalibreIndexer` | `indexing_queue.py` | Indexes ebooks from Calibre libraries with rich metadata enrichment |
| `GitRepoIndexer` | `indexing_queue.py`, `ProjectIndexer` | Indexes code files (tree-sitter) and optionally commit history |
| `RSSIndexer` | `indexing_queue.py` | Indexes RSS articles from NetNewsWire with watermark-based incrementality |
| `ProjectIndexer` | `indexing_queue.py` | Auto-discovers vaults/repos, delegates to specialized indexers, indexes leftovers |
| `EXTENSION_MAP` | `format_routing.py`, `project.py`, `obsidian.py` | Maps file extensions to source types; canonical definition in `format_routing.py` |
| `SUPPORTED_EXTENSIONS` | `format_routing.py` | Frozenset of all indexable file extensions (document + code) |
| `is_supported_extension()` | `format_routing.py`, re-exported by `project.py` | Checks if a file extension is supported for indexing |
| `parse_and_chunk()` | `format_routing.py`, `project.py`, `obsidian.py` | Routes files to the correct parser/chunker pipeline by source type |
| `_SUPPORTED_EXTENSIONS` | Core (`watcher.py`) | Backward-compat re-export from `project.py`; delegates to `format_routing.SUPPORTED_EXTENSIONS` |

## Invariants

| ID | Invariant | Why It Matters |
|---|---|---|
| INV-1 | `upsert_source_with_chunks()` is atomic: delete old documents/vectors, insert new ones, commit in one transaction | Partial writes leave the index in an inconsistent state with orphan vectors or missing documents |
| INV-2 | Every source maps to 1+ documents; every document maps to exactly 1 embedding vector | Search relies on joining sources -> documents -> vec_documents; broken chains produce phantom or missing results |
| INV-3 | File-backed sources use SHA-256 content hash for change detection; virtual sources (email, RSS, commits) use source_path + watermark | Mixing strategies causes either missed updates or unnecessary re-indexing |
| INV-4 | Git repo watermarks stored as JSON dict in `collections.description` (system of record). Email/RSS watermarks computed from `MAX(json_extract(d.metadata, '$.date'))` in documents table; `collections.description` updated with human-readable tracking string as side effect | Watermark loss triggers full re-index; corruption must fall back gracefully |
| INV-5 | `prune_stale_sources()` only removes file-backed sources whose files no longer exist; skips virtual URIs (non-`/` prefix) and sources without file_hash | Pruning virtual sources (email, RSS, calibre descriptions) would permanently delete valid data |
| INV-6 | `ProjectIndexer` excludes repos already covered by explicit `code_groups` to prevent duplicate indexing | Duplicate indexing wastes resources and produces duplicate search results |
| INV-7 | Obsidian indexer skips hidden dirs, `.obsidian`, `.trash`, `.git`, and user-excluded folders | Indexing system/config files pollutes search results with non-content data |
| INV-8 | Database lock retry: 3 attempts with 2s delay for eM Client and NetNewsWire databases | External apps hold locks during normal operation; immediate failure would prevent indexing |
| INV-9 | Per-item errors do not cascade: logged, counted in `IndexResult`, execution continues | One corrupt file or email must not abort the entire indexing run |
| INV-10 | Git indexer routes SPEC.md files to the dedicated spec parser for section-level chunking | SPEC.md files require structural parsing by section, not tree-sitter code parsing |

## Failure Modes

| ID | Symptom | Cause | Fix |
|---|---|---|---|
| FAIL-1 | Indexing returns errors for email/RSS, no new content indexed | External database locked by eM Client or NetNewsWire | Retry 3x with 2s backoff; `IndexResult` records error after exhaustion; close the external app and retry |
| FAIL-2 | Warning logged, file skipped, error count incremented | File deleted between scan pass and index pass | No action needed; next run will prune the stale source via `prune_stale_sources()` |
| FAIL-3 | Orphaned sub-collections persist after directory restructure | Vault or repo marker removed from a project directory | `reconcile_sub_collections()` deletes sub-collections not in current discovery |
| FAIL-4 | `OllamaConnectionError` propagated, `IndexResult` records error | Ollama embedding API timeout or unavailable | Ensure Ollama is running and the configured model is pulled |
| FAIL-5 | Full re-index triggered unexpectedly | Watermark corruption (invalid JSON, unparseable date) | Parser falls back to empty watermarks, triggering full re-index; manual fix by clearing collection description |

## Dependencies

| Dependency | Type | SPEC.md Path |
|---|---|---|
| Parsers (markdown, epub, code, email, rss, calibre, spec) | internal | `src/ragling/parsers/SPEC.md` |
| `db.py` (get_or_create_collection, delete_collection) | internal | `src/ragling/SPEC.md` |
| `embeddings.py` (get_embeddings, serialize_float32) | internal | `src/ragling/SPEC.md` |
| `ragling.document` (Chunk, convert_and_chunk, chunk_with_hybrid, bridges) | internal | `src/ragling/document/SPEC.md` |
| `config.py` (Config) | internal | `src/ragling/SPEC.md` |
| `doc_store.py` (DocStore) | internal | `src/ragling/SPEC.md` |
| `indexing_status.py` (IndexingStatus) | internal | `src/ragling/SPEC.md` |
| `indexer_types.py` (IndexerType) | internal | `src/ragling/SPEC.md` |
| Ollama (embedding API) | external | N/A |
| tree-sitter (code parsing) | external | N/A |
| git CLI | external | N/A |
---
# Parsers

## Purpose

Format-specific content extraction for indexing. Each parser converts an external
data source into a structured domain object that indexers consume. Parsers validate
input, extract text, clean content, enrich with metadata, and return typed objects.
All parsers are read-only — they never modify source data.

The key design decision: parsers return domain-specific dataclasses (not raw text),
letting indexers handle chunking and embedding. The one exception is `spec.py`,
which produces `Chunk` objects directly because SPEC.md section structure maps
naturally to chunk boundaries.

## Core Mechanism

Each parser validates input, extracts structure, cleans text, enriches metadata,
and returns a typed domain object. Parsers never raise exceptions — errors are
logged and `None` or empty collections returned. The one exception is `spec.py`,
which produces `Chunk` objects directly because SPEC.md sections map naturally
to chunk boundaries.

**Key files:**
- `__init__.py` -- `open_ro()` utility for read-only SQLite access
- `markdown.py` -- Obsidian-flavored markdown with frontmatter, wikilinks, tags
- `epub.py` -- EPUB chapter extraction via ZIP archive, OPF manifest, and spine order
- `email.py` -- eM Client SQLite database parsing (.NET ticks, address types, FTI)
- `calibre.py` -- Calibre library metadata loading from metadata.db
- `code.py` -- Tree-sitter structural code parsing (48 extensions + 2 filename patterns, 36 languages). Symbol name extraction and symbol type classification use registry-based dispatch for extensibility.
- `rss.py` -- NetNewsWire RSS article parsing from DB.sqlite3 and FeedMetadata.plist
- `spec.py` -- SPEC.md section-level chunking into typed Chunk objects

**Parser output types:**
- `markdown.py` returns `MarkdownDocument` (title, body_text, frontmatter, tags, links)
- `epub.py` returns `list[tuple[int, str]]` (chapter_number, text) ordered by OPF spine
- `email.py` yields `Iterator[EmailMessage]` (subject, body, sender, recipients, date, folder)
- `calibre.py` returns `list[CalibreBook]` (full metadata: authors, tags, series, formats)
- `code.py` returns `CodeDocument | None` containing `CodeBlock` objects per structural unit
- `rss.py` yields `Iterator[Article]` (title, body, url, feed_name, authors, date)
- `spec.py` returns `list[Chunk]` with subsystem_name, section_type, spec_path metadata

## Public Interface

| Export | Used By | Contract |
|---|---|---|
| `open_ro(db_path)` | email.py, calibre.py, rss.py | Opens SQLite in read-only mode (`?mode=ro`), returns `Connection` or `None` on failure |
| `parse_markdown(text, filename)` | project indexer | Returns `MarkdownDocument` with extracted frontmatter, wikilinks, tags |
| `parse_epub(path)` | calibre indexer, project indexer | Returns `list[tuple[int, str]]` of (chapter_number, text) in spine order |
| `parse_emails(account_dir, since_date?)` | email indexer | Yields `EmailMessage` objects; `since_date` filters by .NET ticks |
| `parse_calibre_library(library_path)` | calibre indexer | Returns `list[CalibreBook]` with full metadata from metadata.db |
| `parse_code_file(file_path, language, relative_path)` | git indexer | Returns `CodeDocument` with structural `CodeBlock` list, or `None` on failure |
| `parse_articles(account_dir, since_ts?)` | RSS indexer | Yields `Article` objects; `since_ts` filters by Unix timestamp |
| `parse_spec(text, relative_path, chunk_size_tokens?)` | git indexer, project indexer | Returns `list[Chunk]` with section-level metadata (subsystem, section_type, spec_path) |
| `find_nearest_spec(file_path, repo_root)` | git indexer | Walks up directory tree to find nearest SPEC.md, returns relative path or `None` |
| `is_spec_file(path)` | git indexer, project indexer | Returns `True` if filename is exactly `SPEC.md` (case-sensitive) |
| `is_code_file(path)` | git indexer, project indexer | Returns `True` if extension or filename matches a supported code language |
| `get_language(path)` | git indexer | Returns tree-sitter language name string, or `None` for unsupported files |

## Invariants

| ID | Invariant | Why It Matters |
|---|---|---|
| INV-1 | All SQLite databases opened in read-only mode (`?mode=ro` URI) | Prevents accidental writes to eM Client, Calibre, and NetNewsWire databases |
| INV-2 | UTF-8 decoding uses `errors="replace"` for binary content | Graceful handling of malformed bytes in EPUB chapters and code files |
| INV-3 | Code blocks use 1-based line numbers (converted from tree-sitter's 0-based) | Matches human-readable file line numbers for search results and navigation |
| INV-4 | SPEC.md H2 headings must match `_SECTION_MAP` keys for correct section_type | Unknown headings get section_type "other" instead of a known classification |
| INV-5 | Parsers never raise exceptions to callers — errors logged, empty/None returned | Indexers can process large batches without one bad file aborting the run |
| INV-6 | Markdown tags are deduplicated; heading lines are never treated as tags | Prevents duplicate tag entries and false positives from `#` in headings |
| INV-7 | EPUB chapters ordered by OPF spine (canonical reading order) | Chunks appear in the author's intended sequence, not filesystem order |
| INV-8 | Email IDs generated via SHA-256 hash of sender, subject, date if missing | Ensures stable deduplication even when eM Client omits the messageId field |

## Failure Modes

| ID | Symptom | Cause | Fix |
|---|---|---|---|
| FAIL-1 | `open_ro()` returns `None`, parser yields nothing | Database locked by eM Client or NetNewsWire | Close the app or wait; indexer retries on next run |
| FAIL-2 | `parse_code_file()` returns `None` | Tree-sitter parse failure (corrupted syntax, missing grammar) | Logged and skipped; file excluded from index |
| FAIL-3 | `parse_epub()` returns empty list | EPUB is DRM-protected or not a valid ZIP archive | Book excluded from index; log message indicates possible DRM |
| FAIL-4 | Chunk has section_type "other" | Unknown H2 heading in SPEC.md not in `_SECTION_MAP` | Add heading to `_SECTION_MAP` or use a standard heading |
| FAIL-5 | `parse_markdown()` returns empty frontmatter | Invalid YAML in frontmatter block | Logged as warning; title falls back to filename stem |

## Dependencies

| Dependency | Type | SPEC.md Path |
|---|---|---|
| `ragling.document.chunker` (Chunk, `split_into_windows`, `word_count`) | internal | `src/ragling/document/SPEC.md` -- `spec.py` imports Chunk plus public helpers for window splitting and word counting |
| PyYAML | external | N/A |
| BeautifulSoup (bs4) | external | N/A |
| tree-sitter-language-pack | external | N/A |
---
# Search

## Purpose

Hybrid vector + full-text search with Reciprocal Rank Fusion. Combines
sqlite-vec embedding distance with FTS5 keyword matching, merges ranked lists
via RRF, and marks stale results whose source files have changed.

## Core Mechanism

Hybrid search runs vector (sqlite-vec) and keyword (FTS5) queries in parallel,
then merges via Reciprocal Rank Fusion with configurable weights (default:
vector 0.7, FTS 0.3, k=60). Stale results are detected by comparing file
mtime to indexed timestamp.

**Key files:**
- `search.py` -- hybrid vector + FTS search with RRF
- `search_utils.py` -- FTS query escaping

## Public Interface

| Export | Used By | Contract |
|---|---|---|
| `search(conn, query, config, ...)` | MCP server, CLI | Returns `list[SearchResult]` with RRF-merged hybrid results |
| `perform_search(query, filters, config)` | MCP server | High-level search across groups; returns `list[SearchResult]` |
| `perform_batch_search(queries, config)` | MCP server | Batch search; returns `list[list[SearchResult]]` |
| `SearchResult` | MCP server | Dataclass for search output with score, stale flag, metadata |
| `SearchFilters` | MCP server | Dataclass for search input filters (collection, source_type, dates, etc.) |
| `BatchQuery` | MCP server | Dataclass wrapping query + filters for batch search |
| `rrf_merge(vector_results, fts_results, ...)` | Tests, search.py | Merges two ranked lists by Reciprocal Rank Fusion |
| `escape_fts_query(query)` | search.py | Wraps query in quotes, doubles internal quotes per FTS5 spec |

## Invariants

| ID | Invariant | Why It Matters |
|---|---|---|
| INV-6 | `rrf_merge()` produces scores that decrease monotonically when iterated in order | Callers rely on results being sorted by relevance |

## Failure Modes

| ID | Symptom | Cause | Fix |
|---|---|---|---|
| FAIL-3 | Search returns stale results marked `stale=True` | Source file modified or deleted after indexing | Re-index the affected collection; stale marking is informational |

## Dependencies

| Dependency | Type | SPEC.md Path |
|---|---|---|
| `config.py` (Config) | internal | `src/ragling/SPEC.md` |
| `db.py` (get_connection, init_db) | internal | `src/ragling/SPEC.md` |
| `embeddings.py` (get_embedding) | internal | `src/ragling/SPEC.md` |
| sqlite-vec | external | N/A -- SQLite extension for vector similarity search |
---
# Watchers

## Purpose

Filesystem, system database, and config file change monitoring. Detects
changes in configured directories, external SQLite databases, and the
ragling config file, routing events to the indexing pipeline.

## Core Mechanism

Filesystem monitoring uses watchdog with a 2-second debounced queue to batch
rapid changes. External SQLite databases (email, calibre, RSS) are polled with
10-second debounce. Config file changes are debounced at 2 seconds with safe
fallback to old config on parse errors.

**Key files:**
- `watcher.py` -- filesystem change monitoring with debounced queue
- `system_watcher.py` -- external database monitoring
- `config_watcher.py` -- config file reload

## Public Interface

| Export | Used By | Contract |
|---|---|---|
| `start_watcher(config, callback)` | CLI (serve) | Returns watchdog Observer monitoring configured paths |
| `get_watch_paths(config)` | CLI (serve), `start_watcher()` | Returns deduplicated list of paths to watch |
| `DebouncedIndexQueue` | `start_watcher()` internal | 2-second debounced callback queue (not exported from package) |
| `start_system_watcher(config, callback)` | CLI (serve) | Returns `SystemCollectionWatcher` for external DB monitoring |
| `SystemCollectionWatcher` | CLI (serve) | Monitors email/calibre/RSS databases with 10-second debounce |
| `ConfigWatcher` | CLI (serve) | Debounced config reload with `get_config()` |

## Invariants

| ID | Invariant | Why It Matters |
|---|---|---|
| INV-10 | `_Handler` filters events by file extension (case-insensitive) and skips hidden directories (except `.git/HEAD` and `.git/refs/`) | Prevents indexing binary files, editor temps, and noisy dotfile churn |
| INV-11 | `get_watch_paths()` deduplicates paths that appear in multiple config sources | Prevents duplicate watchdog observers on the same directory |

## Failure Modes

| ID | Symptom | Cause | Fix |
|---|---|---|---|
| FAIL-6 | Config reload ignored after file change | ConfigWatcher debounce timer not expired; or parse error in new config | Check logs for parse errors; old config preserved on error |

## Dependencies

| Dependency | Type | SPEC.md Path |
|---|---|---|
| `config.py` (Config) | internal | `src/ragling/SPEC.md` |
| `indexer_types.py` (IndexerType) | internal | `src/ragling/SPEC.md` |
| `indexing_queue.py` (IndexingQueue, IndexJob) | internal | `src/ragling/SPEC.md` |
| watchdog | external | N/A -- filesystem event monitoring |
