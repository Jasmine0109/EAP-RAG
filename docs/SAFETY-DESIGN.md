# Safety Design: capabilities and hard boundaries

## 0. Architecture judgment

RAG is good at "retrieve + summarize"; its natural output is "here is an article". Real self-help needs **structured, stateful, paced interaction** (a skill), not one-shot text. So the system has two layers:

- **Knowledge layer**: RAG over authoritative passages, generating cited answers for "what / why / what can I do" questions.
- **Skill layer**: pre-built, reviewed interactive flows for intervention-style requests; RAG only supplies the evidence attached to the flow, not the flow itself.

Anything marked "skill layer" must not be improvised by retrieval.

## 1. Self-help skills that actually help

### 1.1 Structured breathing / relaxation (skill layer)
Down-regulates physiological arousal and interrupts the "anxiety → symptoms → more anxiety" loop.
Deliver as a paced guide (box breathing 4-4-4-4, 4-7-8, PMR), step by step with timing, ≤3 minutes, ending with a 0–10 tension check.

### 1.2 Cognitive restructuring (skill layer, CBT core)
Make automatic negative thoughts explicit, name the distortion (catastrophizing, all-or-nothing, mind-reading, should-statements), and build a balanced alternative.
Use a **thought record** flow: situation → automatic thought → emotion (0–100) → evidence for → evidence against → alternative thought → re-rate emotion.
Socratic, one question at a time; never conclude for the user.

### 1.3 Structured self-screening (PHQ-9 / GAD-7 style, skill layer)
Turns "am I broken?" into a discussable score and a next action.
Ask item by item, auto-score, give a banded result with banded advice. **Always state: this is a screening tool, not a diagnosis.**
Independent trigger: any non-zero answer to PHQ-9 item 9 (self-harm/suicide) → crisis escalation, regardless of total score.
Put **functional impairment** above the number.

### 1.4 Actionable action lists (knowledge + skill)
Translate "exercise more / sleep earlier / cheer up" into small, specific, do-it-now steps (behavioral activation).
Format: specific time + situation + minimum viable action. ≤3 items per list.

### 1.5 "When to seek help" signals (cross-cutting)
- **Red (seek help now)**: self-harm/suicide thoughts, plans, or intent; feeling unable to cope.
- **Yellow (professional evaluation soon)**: symptoms ≥2 weeks with clear impact on work/sleep/relationships; dependence signs; hallucinations.
- **Green (self-help first)**: short duration, clear trigger, functioning intact.

## 2. Hard boundaries (never output)

- **Diagnosis**: no DSM/ICD labels, no "you have depression/anxiety/bipolar", no prognosis.
- **Medication**: no drug names, doses, side effects, or stop/switch advice; always "follow your prescriber, do not change on your own".
- **Treatment**: no individualized treatment plans, no "do CBT / take medication / be hospitalized", no claims of cure, no pretending to be therapy.
- **Crisis**: escalate only. Do not ask for method/time/place, do not analyze, negotiate, lecture, minimize, or judge.
- **Ethics**: no blaming or shaming; no false promises of confidentiality where mandatory reporting applies; no fabricated authority or data; every claim needs a source.

Enforcement: put the forbidden list in the system prompt as a hard constraint, **and** add an output-side keyword/rule check (especially crisis words) that overrides the model.

## 3. Crisis escalation (safe and warm)

Principles:
1. One shot, no back-and-forth.
2. Acknowledge first, then give the action.
3. No interrogation, no "think of your family" pressure.
4. Give a **specific human + a specific number**, not "try to relax".
5. Verify numbers before launch and note service hours.

Script (US):

> I can hear how much pain you're in, and I'm glad you told me. That took courage.
>
> Your safety matters most right now. I can't replace professional crisis support, but these lines are staffed 24/7 by trained people:
>
> - **988 Suicide & Crisis Lifeline** — call or text **988**
> - **SAMHSA National Helpline** — **1-800-662-4357**
> - **Emergency** — call **911**
>
> If you are in immediate danger, call 911 and try to stay with someone you trust.
> Would you be willing to call one of these numbers now?

If the user says they already called or has someone with them: confirm safety, gently leave the door open, do not push.

## 4. MVP priority

| Priority | Capability | Why |
| --- | --- | --- |
| P0 | Safety guardrails + crisis escalation; "when to seek help" signals | safety is the floor |
| P0.5 | Structured self-screening (with disclaimer) | real value + a natural route to help |
| P1 | Breathing/grounding; thought record; action list | the three highest-frequency situations |
| P2 | Mindfulness, workplace scripts, policy retrieval, light follow-up | retention and coverage |
