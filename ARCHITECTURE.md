# Matching Agent - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     MATCHING AGENT SYSTEM                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│   Job Input     │
│  (from Browser  │
│     Agent)      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                         JobMatcher                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Stage 1: Keyword Filter (Fast, Free)                  │    │
│  │  ─────────────────────────────────────────             │    │
│  │  • Check excluded locations (Israel)                   │    │
│  │  • Validate company size (1-200 employees)             │    │
│  │  • Check excluded keywords                             │    │
│  │  • Count profile keyword matches (min 2)               │    │
│  │                                                         │    │
│  │  Result: PASS → Continue | FAIL → REJECTED             │    │
│  └────────────────────────────────────────────────────────┘    │
│                           ↓                                      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Stage 2: LLM Scoring (Smart, $$$)                     │    │
│  │  ────────────────────────────────────                  │    │
│  │  • Build prompt with job + resume                      │    │
│  │  • Call Claude API (Sonnet 3.5)                        │    │
│  │  • Parse JSON response:                                │    │
│  │    - Score: 0-100                                      │    │
│  │    - Reasoning: explanation                            │    │
│  │    - Key matches: ["skill1", "skill2"]                 │    │
│  │    - Concerns: ["gap1", "gap2"]                        │    │
│  │                                                         │    │
│  │  Result: score >= 60 → MATCHED | score < 60 → REJECTED │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
         Score < 60                  Score >= 60
                │                         │
                ▼                         ▼
         ┌────────────┐          ┌──────────────┐
         │  REJECTED  │          │   MATCHED    │
         │  (logged)  │          │ (ready to    │
         └────────────┘          │   apply)     │
                                 └──────┬───────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                        EasyApplyBot                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Navigate to Job Page                                        │
│     └─ Open LinkedIn job URL                                    │
│                                                                  │
│  2. Click Easy Apply Button                                     │
│     └─ Find and click button, wait for modal                    │
│                                                                  │
│  3. Multi-Page Form Handling                                    │
│     ├─ Fill standard fields (phone, email)                      │
│     ├─ Detect custom questions                                  │
│     ├─ Generate answers via JobMatcher.answer_question()        │
│     ├─ Fill custom question fields                              │
│     └─ Click "Next" → Repeat until final page                   │
│                                                                  │
│  4. Submit Application                                          │
│     ├─ Click "Submit application"                               │
│     ├─ Verify success message                                   │
│     └─ Wait random delay (30-90s)                               │
│                                                                  │
│  5. Record Application                                          │
│     └─ Save to database with timestamp, questions, status       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Interaction Flow

```
UserProfile ──┐
              ├──> JobMatcher ──┐
SearchCriteria┘                 │
                                ├──> match_job(job)
Job ────────────────────────────┘         │
                                          ├─> keyword_filter()
                                          ├─> score_job_match() ──> Claude API
                                          │
                                          ▼
                                    (Job, is_match)
                                          │
                            is_match = True│
                                          ▼
                                    EasyApplyBot
                                          │
                                          ├─> apply_to_job()
                                          ├─> answer_question() ──> Claude API
                                          │
                                          ▼
                                    Application Record
```

## Data Flow

```
┌──────────────┐
│ UserProfile  │
│ ────────────│
│ • Name       │
│ • Skills     │
│ • Experience │
│ • Education  │
└──────┬───────┘
       │
       │ provides context
       │
       ▼
┌──────────────────────┐        ┌──────────────┐
│     JobMatcher       │───────>│  Claude API  │
│ ──────────────────── │ prompt │ ────────────│
│ • profile_keywords   │<───────│ • Scoring    │
│ • criteria           │response│ • Q&A        │
│ • client (Anthropic) │        └──────────────┘
└──────────┬───────────┘
           │
           │ scores & updates
           │
           ▼
┌──────────────────────┐
│        Job           │
│ ──────────────────── │
│ • title, company     │
│ • description        │
│ • match_score ────┐  │
│ • match_reasoning │  │
│ • key_matches     │◄─┴─ Updated by matcher
│ • concerns        │    │
│ • status ─────────┼────┘
└──────────┬───────────┘
           │
           │ if matched
           │
           ▼
┌──────────────────────┐
│   EasyApplyBot       │
│ ──────────────────── │
│ • page (Playwright)  │
│ • profile            │
│ • matcher ───────────┼──> For answering questions
└──────────┬───────────┘
           │
           │ creates
           │
           ▼
┌──────────────────────┐
│    Application       │
│ ──────────────────── │
│ • job_id             │
│ • status             │
│ • submitted_at       │
│ • custom_questions   │
│ • notes              │
└──────────────────────┘
```

## Scoring Algorithm

```python
def match_job(job: Job) -> (Job, bool):
    """
    Two-stage matching pipeline

    Stage 1: Keyword Filter (0.1ms, $0)
    ────────────────────────────────────
    - Location check
    - Company size check
    - Keyword counting

    ~80% of jobs filtered out here

    Stage 2: LLM Scoring (500ms, $0.0015)
    ──────────────────────────────────────
    - Build prompt (job + resume)
    - Claude API call
    - Parse score & reasoning

    Only ~20% of jobs reach this stage

    Decision
    ────────
    score >= min_match_score → MATCHED
    score <  min_match_score → REJECTED
    """
```

## Question Answering Flow

```
Application Form
    │
    ├─> Standard Fields (name, email, phone)
    │   └─> Auto-fill from UserProfile
    │
    └─> Custom Questions
        │
        ├─> Question 1: "Why this role?"
        │   │
        │   ├─> Extract question text
        │   ├─> JobMatcher.answer_application_question(q)
        │   │   │
        │   │   ├─> Build prompt with profile context
        │   │   ├─> Claude API call
        │   │   └─> Return answer
        │   │
        │   └─> Type answer into field (human-like speed)
        │
        ├─> Question 2: "Your experience with..."
        │   └─> [Same flow]
        │
        └─> Continue for all questions
            │
            └─> Submit application
```

## Error Handling Strategy

```
┌─────────────────────┐
│  Operation Start    │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │  Try Block   │
    └──────┬───────┘
           │
    ┌──────▼────────────────────────┐
    │                               │
    ▼                               ▼
Success                         Exception
    │                               │
    ▼                               ▼
┌─────────┐                ┌────────────────┐
│ Return  │                │ Log Error      │
│ Result  │                │ with details   │
└─────────┘                └────────┬───────┘
                                    │
                           ┌────────▼─────────┐
                           │                  │
                           ▼                  ▼
                    Critical Error     Recoverable Error
                           │                  │
                           ▼                  ▼
                    ┌─────────────┐   ┌──────────────┐
                    │ Return low  │   │ Use fallback │
                    │ score (0)   │   │ or skip      │
                    └─────────────┘   └──────────────┘
                           │                  │
                           └────────┬─────────┘
                                    │
                                    ▼
                            ┌───────────────┐
                            │ Continue with │
                            │  next job     │
                            └───────────────┘
```

## Rate Limiting

```
Application Flow with Rate Limiting
────────────────────────────────────

Job 1 → Apply → [Random Delay 30-90s] ┐
                                       │
Job 2 → Apply → [Random Delay 30-90s] ├─> Daily Counter
                                       │
Job 3 → Apply → [Random Delay 30-90s] │
                                       ▼
...                              ┌──────────────┐
                                 │ Applications │
Job 24 → Apply → Delay           │   Today: 24  │
                                 └──────────────┘
Job 25 → Apply → Delay                 │
                                       ▼
Job 26 → ❌ BLOCKED          ┌──────────────────┐
         "Max 25/day"         │  Hit Daily Limit │
                              │   Wait until     │
                              │   next day       │
                              └──────────────────┘
```

## Cost Optimization

```
100 Jobs Input
    │
    ├─> Keyword Filter (Stage 1)
    │   • Cost: $0
    │   • Time: ~100ms total (1ms each)
    │   • Filter out: 80 jobs (80%)
    │
    └─> Remaining: 20 jobs
        │
        └─> LLM Scoring (Stage 2)
            • Cost: 20 × $0.0015 = $0.03
            • Time: 20 × 500ms = 10s
            • Result: ~10 matched, ~10 rejected

Total Cost: $0.03 for 100 jobs
Total Time: 10 seconds
Efficiency: 80% cost reduction vs. scoring all jobs
```

## Integration Points

```
┌────────────────────────────────────────────────────────┐
│                    Full System                          │
├────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐                                      │
│  │ CORE Agent   │                                      │
│  │ ────────────│                                      │
│  │ • Database   │◄─────────────────┐                  │
│  │ • Config     │                  │                  │
│  │ • CLI        │                  │                  │
│  └──────┬───────┘                  │                  │
│         │                           │                  │
│         │ config                    │ save             │
│         │                           │                  │
│  ┌──────▼───────┐          ┌───────┴──────┐          │
│  │ BROWSER      │          │  MATCHING    │          │
│  │ Agent        │          │  Agent       │          │
│  │ ────────────│  jobs    │ ────────────│          │
│  │ • LinkedIn   ├─────────>│ • JobMatcher │          │
│  │   Scraper    │          │ • EasyApply  │          │
│  │ • Job Search │          │ • Scoring    │          │
│  │ • Navigation │◄─────────┤ • Application│          │
│  └──────────────┘  page    └──────────────┘          │
│                     object                             │
│  ┌──────────────┐                                      │
│  │ RESUME Agent │                                      │
│  │ ────────────│                                      │
│  │ • PDF Parser ├───────────┐                         │
│  │ • Profile    │  profile   │                         │
│  └──────────────┘           │                         │
│                              │                         │
│                     ┌────────▼─────────┐              │
│                     │   UserProfile    │              │
│                     │   (used by       │              │
│                     │   JobMatcher)    │              │
│                     └──────────────────┘              │
└────────────────────────────────────────────────────────┘
```

## State Machine (Job Status)

```
           ┌─────────────────────────────────┐
           │          FOUND                  │
           │ (Job discovered by BROWSER)     │
           └───────────┬─────────────────────┘
                       │
                       │ keyword_filter()
                       │
            ┌──────────┴──────────┐
            │                     │
         PASS                  FAIL
            │                     │
            ▼                     ▼
    ┌───────────────┐     ┌────────────┐
    │   FILTERED    │     │  REJECTED  │
    │               │     │ (logged)   │
    └───────┬───────┘     └────────────┘
            │
            │ score_job_match()
            │
     ┌──────┴──────┐
     │             │
  score >= 60   score < 60
     │             │
     ▼             ▼
┌──────────┐  ┌────────────┐
│ MATCHED  │  │  REJECTED  │
│          │  │            │
└────┬─────┘  └────────────┘
     │
     │ apply_to_job()
     │
     ▼
┌──────────┐
│ APPLIED  │
│          │
└────┬─────┘
     │
     │ (user updates)
     │
     ├────────────────┬─────────────┬──────────┐
     ▼                ▼             ▼          ▼
┌──────────┐  ┌─────────────┐ ┌────────┐ ┌────────┐
│INTERVIEW-│  │  REJECTED   │ │OFFERED │ │ CLOSED │
│   ING    │  │             │ │        │ │        │
└──────────┘  └─────────────┘ └────────┘ └────────┘
```

## Key Metrics

```
Performance Metrics
───────────────────
• Keyword Filter: ~1ms per job
• LLM Scoring: ~500ms per job
• Application: ~30-90s per job (with delays)

Cost Metrics
────────────
• Keyword Filter: $0 per job
• LLM Scoring: ~$0.0015 per job
• Daily cost (25 apps): ~$0.50-1.00

Efficiency Metrics
──────────────────
• Filter rate: ~80% jobs filtered
• Match rate: ~50% of scored jobs match
• Overall: ~10% of all jobs matched
```

## Security & Privacy

```
┌────────────────────────────────────┐
│       Sensitive Data Flow          │
└────────────────────────────────────┘

API Keys
────────
• Stored in: .env file (gitignored)
• Accessed via: os.getenv()
• Never logged or committed

User Profile
────────────
• Contains: PII (name, email, phone)
• Sent to: Claude API (encrypted HTTPS)
• Stored: Local database only
• Privacy: Anthropic policy applies

LinkedIn Credentials
────────────────────
• Stored in: .env file (gitignored)
• Used by: BROWSER agent for login
• Never sent to Claude API

Application Data
────────────────
• Stored: Local SQLite database
• Contains: Company names, questions, answers
• Backup: User responsibility
```
