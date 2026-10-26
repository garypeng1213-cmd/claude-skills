# 全域 CLAUDE.md — Gary

## 每次對話開始一律載入這些 skill（2026-07-08 起）

不管開啟什麼對話、什麼專案，開場第一件事就是用 `Skill` 工具把以下技能載入，再回應使用者：

1. `/using-superpowers`
2. `/graphify`
3. `/ui-ux-pro-max`
4. `/frontend-design`
5. `/canvas-design`
6. `/planning-with-files`

（`/using-superpowers` 一定第一個載入，它負責建立找 skill、用 skill 的規矩。）

（`/graphify` 自 2026-08-16 起加入常駐載入清單：不管有沒有 `graphify-out/`，開場就把它載入，之後任何「這個 codebase 怎麼運作 / 檔案關係 / 專案內容」的問題一律先當 graphify 查詢處理。）

## 每次任務結束自動推送（2026-07-12 起）

- 每次任務結束後，直接把成果 commit 並 `git push` 到遠端，**不用先問我**。
- 只有在「沒得推送」時才跳提示告訴我，例如：
  - 完全沒有任何變更（沒東西可 commit、也沒有未推送的 commit）
  - 不是 git repo，或沒有設定 remote
  - push 失敗（認證問題、被 reject 需要先 pull 等）——說明原因並等我指示。

## 驗證分級（2026-10-11 起）

這一段優先於下方 pilotfish 的 Orchestration 區塊：該區塊把 `release` 一律列為 independent-review trigger，以這裡的分級為準。區塊內的文字由 pilotfish 管理，不要直接改它。

- **只改畫面、樣式、文件的變更**（沒有動到安全規則、權限、認證、金鑰、資料結構）：上線不算 independent-review trigger。主對話自己跑相關測試通過就可以，不另外送 `plan-verifier`、`verifier`；回報時講明「這次沒有送獨立驗證」。
- **改安全規則或部署安全規則**（例如 Firebase 的 `database.rules.json`、權限、認證、金鑰）：維持完整流程——唯讀安全審查 → 計畫審查 → 我核准 → `security-executor` → 獨立 `verifier` → 才部署。
- **驗證沒過、但問題只在文件或註解的用字**：直接改掉並向我說明，不再送一輪重驗。
- 其餘情形照 Orchestration 區塊原文。
- 這裡省掉的是獨立驗證，不是我的同意：併 main、部署、任何對外動作仍然要我說可以才做。

## 技能路由速查表（2026-07-06 整併後：本機 18 件 + 內建）

| 要做什麼 | 用哪個 |
|---|---|
| 開始任何新任務/新功能 | `/using-superpowers` → brainstorming → writing-plans → executing-plans |
| 建/改 UI | `frontend-design`（實作）；`ui-ux-pro-max`（只在選風格/配色/字體時查表） |
| 除錯、測試失敗 | `systematic-debugging` |
| 寫功能/修 bug | `test-driven-development` |
| 跑 code review | 內建 `/code-review`；流程紀律用 `requesting-code-review` / `receiving-code-review` |
| 宣稱完成之前 | `verification-before-completion`；要實跑驗證用內建 `/verify` |
| Word / PDF / 簡報 / 試算表 | 內建 `anthropic-skills:` docx / pdf / pptx / xlsx |
| 排程、循環任務 | 內建 `/schedule`、`/loop` |
| 生圖／改圖（點陣圖：插畫、icon、配圖、素材） | `codex-imagegen`（透過 Codex CLI `image_gen`，預設生圖路徑） |
| 深度研究 | 內建 `deep-research` |
| 建 MCP / 設計 agent 工具 | `mcp-builder`、`tool-design` |
| 問 codebase 架構／檔案關係／專案內容 | `graphify`（開場已常駐載入，直接當查詢用） |

- 封存的技能在 `~/.claude/skills-archive/`（整個資料夾搬回 `~/.claude/skills/` 即重新啟用）。
- 整併前完整備份：`~/.claude/skills.bak-20260706`。
- 完整盤點與決策記錄：和旺專案 `docs/skills_audit_2026-07-06.md`。
- 新工具一律走官方 plugin marketplace 安裝，不要手動複製目錄。


<!-- pilotfish:begin -->
<!-- pilotfish v1.3.10 -->
## Orchestration

Main-session policy. Named roles (`scout`, `Explore`, `plan-verifier`, `security-reviewer`, `mech-executor`, `executor`, `verifier`, `security-executor`): ignore this section, perform assigned task, never spawn subagents.

Main session owns framing, architecture, ambiguity, Plan synthesis, approval, integration, final judgment. Roles supply bounded discovery, execution, fresh-context review.

### Routing and lifecycle

- Interaction shape precedes Baton/lifecycle/worker routing. Choose first match: `co_discover` when outcome/acceptance is unclear; `explore_then_plan` when otherwise-clear direction is broad/high-impact; `execute` for an otherwise-clear bounded outcome. `co_discover` asks only direction-changing questions or uses the smallest reversible probe. Routing controls interaction; approval controls authority.
  **`explore_then_plan` boundary:** its first turn is `discovery_read_only` despite imperative implementation wording. Inspect only; Write/Edit/NotebookEdit and mutating Bash are forbidden. Return assumptions and one reversible slice; label `next_gate: user_approval` only after every applicable readiness gate is `READY`, otherwise label the blocking or paused gate, then end the turn. Execution is unreachable until later explicit approval. Stop discovery when more evidence cannot change next gate.
- After shape selection, inspect available skills. Large/architectural/risky/cross-surface task + listed `baton-dispatch` → invoke before dispatch brake/direct-vs-delegated choice; never pre-screen it away. Baton may still choose direct work and may shape questions, topology, worker count, ownership, stops. If absent, apply this policy without searching/installing. pilotfish and Baton compose; neither bypasses the other's named-role, model-routing, leaf, approval, or verification boundaries.
- Risk precedes size. Independent-review triggers: explicit user request for independent review; security/trust; destructive/irreversible/external mutation; data/schema/serialization/migration; release; material cross-component acceptance. File count, model concern, routine docs/UI, bounded fail-soft bug alone do not trigger.
- Without a risk trigger, small/local/stable work stays direct; cross-file repetition is not small. Otherwise use phase-aware lifecycle below.
- Discovery gate: stable question, scope, evidence format, stop; outcome/Plan may remain unknown. Eligible delegation: bounded read-only `scout`/`Explore` across disjoint evidence surfaces reducing Plan uncertainty.
- Plan gate: main synthesizes one Plan. Large work uses program envelope plus independently approvable slices carrying stable ID, outcome, scope, non-goals, owners, prerequisites, acceptance proving outcome, rollback, budget, stops. Risk-triggered units use fresh `plan-verifier`; main owns revisions/synthesis.
- Approval gate: large/architectural/risky/plan-first work presents Plan and waits for explicit approval. Broad initial request is not approval of unseen Plan. No source edit or implementation brief before required approval; read-only clarification remains allowed.
- Execution gate: approved contract fixes scope, exclusive ownership, constraints, done criteria, integration, verification. Routes: `mech-executor` for fully specified repetition, `executor` for bounded judgment, `security-executor` for approved security work.
- Verification gate: implementation/integration must be concrete enough to test. Risk-triggered units use fresh `verifier` against exact claim before completion report.

### Dispatch and ownership

- Before every Agent call, state phase and apply dispatch brake. Discovery needs stable research contract, never pre-decided outcome; writing needs stable approved execution contract. Block fan-out when evidence evolves, ownership overlaps, synthesis/verification owner is missing, or integration cost exceeds benefit.
- Bounded task-local search stays main-session work by default, even cross-directory, when splitting duplicates startup/synthesis. Fan out only for genuinely independent substantial surfaces, overlapping latency, or independently gathered evidence/perspectives that materially reduce Plan uncertainty.
- Before discovery launch, declare main-owned versus agent-owned read scopes. Active agent scope is temporarily exclusive until result collection, cancellation, or redirection: main must not read/analyze same scope; later Read/Glob/Grep/Bash must reject mixed commands touching any active-agent path.
- Collect all discovery results before cross-surface comparison. Post-result sanity checks target only decision-carrying facts. Discovery roles report facts; main reconciles evidence and writes Plan.
- Stable same-shape multi-file mechanical repetition defaults to one `mech-executor` with complete one-shot brief, exclusive ownership, independent items, per-item acceptance. Foreground unless possible long command requires background.
- Collect mechanical result before main edits; worker files remain worker-only until completion; never redo worker changes. Main retains per-item triage, exceptions, integration, acceptance.
- Direct main execution of qualifying mechanical work requires prior concrete blocker: evolving/coupled evidence, ownership/integration conflict, worker unavailable, or non-positive net benefit.
- Outside mechanical shape, delegate only when lower cost/quota, preserved context, parallelism, isolated ownership, or fresh-context independence outweigh reconstruction, coordination, integration, verification cost. `executor` handles bounded judgment; `security-executor` approved security work; `mech-executor` fully specified repetition.
- Dispatch brakes judge one call at a time. Recurrence qualifies through stable one-shot brief, not numeric threshold; items must be independent and same shape. Main retains diagnosis, exceptions, integration, acceptance; never batch work coupled to evolving diagnosis.
- Single unknown bug stays main-session work through root-cause discovery, trace-driven debugging, coupled state propagation, patch design, first minimal fix, live verification when one path owns them. Never build sequential `scout`→`executor` pipeline. Scout may answer bounded reusable side question that neither owns nor blocks diagnosis.
- Large cross-surface investigation may use bounded read-only discovery, followed by main Plan synthesis. Executor waits until root cause, scope, files, constraints, done criteria, approval are stable without rediscovery. Diagnosed review finding with known remedy is Execution work and may join independent same-shape findings.
- One-shot spec includes goal, constraints, done criteria, relevant paths, rationale. Use cheapest plausible role; after two failures, escalate tier or take over—no third same-tier retry.
- Security-sensitive work (authn/authz, credentials/secrets, identity/privacy, crypto, validation/hardening, vuln analysis) never uses general executors. Before required approval and first readiness review, finish tool-enforced read-only `security-reviewer`; carry findings/dispositions into Plan. After approval, send stable contract to `security-executor`. Never run both pre-approval reviews concurrently or send pre-approval work to write-capable security executor.
- Any independent-review trigger makes that unit risky: pre-approval `plan-verifier` and post-implementation `verifier` are mandatory Agent calls, with no extra opt-in. Higher-priority prohibition → pause before edits, never direct fallback or waiver; unblock only by lifting the prohibition or narrowing away every trigger. Bounded fail-soft exception applies only without listed risk. After readiness, present Plan and end turn; implementation begins only after explicit approval in a later turn. Plan readiness judges proposed acceptance check.
- Named-role model routing lives in agent definitions. Omit invocation `model`; override would replace role routing. Set `model` only for truly ad-hoc agent and never inherit main-session model accidentally.
- `plan-verifier` reviews one stable envelope/slice and returns **READY** or **REVISE** under its role contract; malformed output is protocol failure. Outcome `verifier` receives exact claim/acceptance plus relevant diff/paths and returns **CONFIRMED**, **REFUTED**, or **INCONCLUSIVE** under its role contract. Never swap roles: Plan review stays read-only; outcome review may use Bash only for post-approval test reproduction.
- Review program envelope before slices, then next executable slice only. Both must be READY before approval; unrelated downstream slices do not block. Shared blockers/unmet prerequisites gate dependents; cosmetic splitting resets nothing.
- Per readiness unit: materially revise after valid `REVISE`, then use fresh reviewer. Two automatic `REVISE` verdicts stop resubmission; main dispositions every blocker as `FIX`, `DEFER`, or `REJECT`, then simplifies, narrows, or splits. Material fix/narrowing/split/evidence-backed disposition changing readiness claim records a new readiness epoch and opens exactly one closing fresh review. Another `REVISE` pauses or escalates; closing review cannot restart loop. Ask user only for unresolved P0/P1, product/authority choice, or unmet original scope—not merely permission for another review round. Cap never means READY; user-directed continuation remains allowed but not default. Never resubmit substantially unchanged Plan.
- Risk-triggered completed work gets one fresh outcome-verifier pass at smallest coherent integration boundary where full claim can be refuted. Run primary user-visible acceptance first; avoid micro-verifier calls. Tests/builds/static checks are intermediate evidence, not review substitutes; review never substitutes for them. Verify earlier at security, cross-language/FFI, serialization/pre-aggregation, irreversible, or integration-blocking boundaries.
- Role verdicts are evidence, never implementation/scope authority. Main checks reproducibility, introduced/in-scope status, exact-claim relevance, priority, confidence before `FIX`/`DEFER`/`REJECT`. Documented deferral or evidence-backed rejection addresses a finding; path overlap alone is irrelevant; implementation-caused regression remains relevant even when omitted from brief. P0 freezes slice/dependents and pauses; automatic containment is limited to agent-owned work/evidence, never external action. P1 requires approved-scope fix or pause. Introduced P2 stays blocking; other P2 fixes only within explicit acceptance, approved scope, bounded change, else defer with rationale and narrow claim. P3/P4 default defer/report; never change a `CONFIRMED` candidate for them or start dedicated fix/reverify loop.
- Never claim blocker fixed without contrary evidence or successful recheck of original failure. Any required post-verdict change invalidates final-byte coverage; when claim-relevant, rerun primary acceptance plus one fresh verifier, otherwise pause. Retry `INCONCLUSIVE` once only after stated missing evidence, contract, prerequisite, or environment materially changes; otherwise pause affected slice. External PR review batch-dispositions every current-head finding; adjacent hardening after acceptance becomes follow-up unless P0/P1, security-relevant, or introduced P2 regression.
- Scout findings are inputs, not verified outcomes: sanity-check or re-scout any decision resting on one scouted fact. Verifier gate covers executor work, never reconnaissance. Do not delegate immediate single-file reads, final decisions, coupled one-path investigation, Plan synthesis, integration judgment, or anything user asked main session to judge personally.

### Recovery and authority

- Severity rules apply every verification run; AUTO/ASK mode selection applies only to likely-long autonomous work. Default recovery: one targeted recheck after reproduced blocker fix—original reproduction plus bounded basic regression, never adjacent-hardening audit. High-risk claim-critical P1/P2 recovery allows at most five meaningful fix/reverify passes; blocking P2 shares that budget and joins next coherent integration-boundary review; rounds 3–5 are emergency recovery, not quota. Each pass needs material change to candidate, claim, acceptance, contract, external evidence/prerequisites, or environment; a verdict/output alone is not change. Fingerprint complete tested identity from committed HEAD, tracked/staged diff, untracked input paths/content, each input submodule HEAD plus recursive working-tree content, and tested-artifact digest when applicable; artifact may replace source identity only as sole deliverable. Never reverify identical state; stop earlier when next pass only searches adjacent risk. After five still-blocking passes, mark `PAUSED_VERIFICATION`, block dependents, continue unrelated approved slices only when risk is not cross-cutting.
- Before likely long autonomous work, offer `AUTO` or `ASK` and wait. Sleeping/eating/leaving never authorizes continuation; explicit “continue while I am away” selects AUTO and must be announced. `/goal` preserves objective only. Headless likely-long run without selected mode emits `PAUSED_NEEDS_USER` and exits.
- `AUTO` permits approved-scope reversible work plus main-session P2 adjudication only. No commit/push/PR/merge/release/publish/install/credential rotation/shutdown/rollback/deletion, external mutation, destructive/irreversible action, scope expansion, or extra-spend authority; separately granted authority remains valid.
- `ASK` uses `AskUserQuestion` when available; otherwise end with `PAUSED_NEEDS_USER`, one concise question, choices, recommendation. Headless/noninteractive run exits—never poll, retry, guess, or continue affected slice. Questions belong to main session, never child. P0 freezes affected slice/dependents; cross-cutting P0 stops program. Stop run only for cross-cutting blocker, all remaining work depending on paused slice, new authority/product decision, destructive/irreversible/external action, exhausted budget/quota, unsafe environment, or unattainable original scope. Final report separates confirmed/fixed/deferred/regraded findings (original/revised priority, evidence, disposition), rejected findings with evidence, paused slices/dependents, inconclusive/unrun checks, narrowed claims, tests/gates/cost, external actions not taken.

### Parallel and runtime mechanics

- Schedule by dependency, not eventual need. When selecting 2+ independent agents, launch all back-to-back with `run_in_background: true` before remaining main work; keep scopes disjoint; allow no interleaved duplicate reconnaissance; collect all results before dependent work/final answer. Foreground only when next action blocks on result, no useful independent work remains, net benefit is positive. Never launch merely to wait when main owns the same evolving evidence more cheaply. Parallel writers use `isolation: "worktree"` (requires Git); without Git, never fan out—use one shared-checkout writer or work direct. Read-only roles may share checkout. Integrate every collected worktree; uncollected worktree means lost work.
- Long-running processes belong to main session. Agent with possible long command runs `run_in_background: true`; Bash-capable leaf roles never detach. Leaf unable to finish bounded foreground work returns exact command, absolute working/worktree directory, environment, input paths; main runs `Bash(run_in_background: true)` in that context, then resumes role with captured output. Liveness comes from tracked task state/output, never CPU/processes/stale files/transcript delay; never kill on suspicion. Subagent final message is deliverable: read completed output directly; resume only for genuinely new/redirected work, never collection/restatement.
<!-- pilotfish:end -->
# graphify
- **graphify** (`~/.claude/skills/graphify/SKILL.md`) - any input to knowledge graph. Trigger: `/graphify`
When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.
- 另見上方「每次對話開始一律載入這些 skill」：graphify 已列為開場常駐載入項（第 2 順位），不必等使用者輸入 `/graphify`。
