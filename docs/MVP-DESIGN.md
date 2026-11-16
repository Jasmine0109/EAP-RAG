# MVP Design

> The smallest product that is still useful: **intake first, then one grounded answer with a micro-action and an escalation path.**

## 0. Conversation flow: intake → explore → safety check → advice

**Rule: do not give advice before you understand what happened, why it hurt, and how the person felt. One question per turn. Never interrogate.**

### State machine

```
user message
  ├─ crisis signal (self-harm / suicide / harm to others) → ESCALATE (no questions)
  └─ otherwise → intake:

  0 safety check   "One important question: have you had thoughts of harming yourself?"
                    ├─ yes → ESCALATE
                    └─ no  → 1
  1 situation      "What happened? Can you tell me more?"
  2 trigger        "What part of it hurts the most?"
  3 details        "What was the situation? What did you do, what did they do?"
  4 feelings       "How did you feel? What was the first thought in your head?" (CBT)
  5 advice         → answer card: empathy + suggestions + micro-action + when to seek help + sources
```

### Rules

| Rule | Detail |
| --- | --- |
| One question per turn | Do not dump five questions |
| Skip what is known | If the user already described the situation, start at "trigger" |
| Min 2, max 5 turns | At the cap, give the best help you can and invite more detail |
| Safety first | Clear crisis signal → escalate, no intake |
| Gentle framing | "One important question…", not an interrogation |
| Yes → escalate | Stop the intake immediately |

### CBT prompts (pick one per turn)

- "What was the first thought that went through your head?"
- "What did this make you think about yourself?"
- "What are you most afraid will happen?"
- "Is there another way to read this?" (cognitive reappraisal, at the advice stage)

### Why intake first

1. Advice without understanding is useless, and sometimes harmful.
2. The CBT chain is **situation → automatic thought → emotion → behavior**; without it there is nothing to work on.
3. The safety check is the floor: earlier detection, earlier escalation.

## 1. Answer card (5 parts)

1. **Empathy** — acknowledge the feeling, no judgment.
2. **Suggestions** — 2–3, each with a citation.
3. **Micro-action** — one thing to do in 1–3 minutes.
4. **When to seek help** — red/yellow flags.
5. **Sources** — expandable citations.

## 2. UI wireframe

```
┌──────────────────────────────────────────────┐
│ 🌿 Support Assistant        prototype · not medical advice │
├──────────────────────────────────────────────┤
│  Assistant: tell me what's going on, I'll help you sort it out. │
│  You: I've been really stressed at work and can't sleep.         │
│                                                              │
│  ┌──────────────────────────────────────────┐                │
│  │ It sounds like you're running on empty.    │                │
│  │ What's been happening at work lately?      │                │
│  └──────────────────────────────────────────┘                │
│  [ type your message…                          ] [send]       │
│  If you or someone else is at risk, call 988.                 │
└──────────────────────────────────────────────┘
```

> The first reply is a **question**, not an answer card. The card comes after intake.

## 3. Example (intake, then advice)

```
Turn 1  You:    "I've been really stressed at work and can't sleep."
        Bot:    "That sounds exhausting. What's been happening at work?"
Turn 2  You:    "My boss keeps assigning work right before I leave."
        Bot:    "What part of that is hardest for you?"
Turn 3  You:    "Feeling like I have no control over my time."
        Bot:    [answer card: empathy + boundary suggestions + micro-action + sources]
```

## 4. Crisis card

```
You are not alone. Please reach out now:
  988 Suicide & Crisis Lifeline (call or text 988)
  Emergency: 911
If you can, tell someone you trust and stay with them.
```

## 5. Scope

In: chat, intake, cited answers, micro-action, crisis escalation.
Out: login, multi-turn memory across sessions, admin dashboard, cloud deploy, non-English UI.

## 6. Deferred to V1

Emotion tagging, structured self-screening (PHQ-9/GAD-7), breathing guides, thought records, workplace scripts, policy retrieval, follow-up nudges.
