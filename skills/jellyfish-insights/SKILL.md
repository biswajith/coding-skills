---
name: jellyfish-insights
description: Surfaces Jellyfish engineering intelligence metrics (DORA, cycle time, PR throughput, AI tool ROI, team delivery health) to inform planning, sprint decisions, and code review context. Use when the user asks about team metrics, delivery performance, sprint health, PR cycle time, AI tool impact, or engineering KPIs.
disable-model-invocation: true
allowed-tools: Bash(curl *), Bash(gh *)
---

# Jellyfish Engineering Insights

Pull engineering intelligence from Jellyfish to inform planning, retrospectives, and delivery decisions.

## Setup: Configure access

Read `.claude/jellyfish.md` for your Jellyfish instance config. If it doesn't exist, ask the user to create it:

```markdown
# .claude/jellyfish.md
JELLYFISH_URL=https://<your-org>.jellyfish.co
JELLYFISH_API_KEY=<your-api-key>
TEAM=<your-team-name-or-id>
```

> Get your API key from Jellyfish → Settings → Integrations → API.
> Keep this file in `.gitignore` — it contains credentials.

If no API key is available (trial/demo account), skip to **Manual Dashboard Mode** below.

## API Mode

When API access is configured, fetch metrics with:

```bash
curl -s -H "Authorization: Bearer $JELLYFISH_API_KEY" \
  "$JELLYFISH_URL/api/v1/metrics?team=$TEAM&period=last_30_days" | python3 -m json.tool
```

### Available metric queries

**DORA metrics (last 30 days):**
```bash
curl -s -H "Authorization: Bearer $JELLYFISH_API_KEY" \
  "$JELLYFISH_URL/api/v1/dora?team=$TEAM"
```

**PR cycle time breakdown:**
```bash
curl -s -H "Authorization: Bearer $JELLYFISH_API_KEY" \
  "$JELLYFISH_URL/api/v1/prs?team=$TEAM&state=merged&limit=50"
```

**AI tool impact (Cursor/Claude Code/Copilot):**
```bash
curl -s -H "Authorization: Bearer $JELLYFISH_API_KEY" \
  "$JELLYFISH_URL/api/v1/ai-tools?team=$TEAM"
```

**Sprint/delivery forecast:**
```bash
curl -s -H "Authorization: Bearer $JELLYFISH_API_KEY" \
  "$JELLYFISH_URL/api/v1/delivery?team=$TEAM"
```

> Note: Jellyfish's API surface varies by plan tier. If an endpoint returns 404 or 403, fall back to Manual Dashboard Mode for that metric.

## Manual Dashboard Mode

When API is not available, guide the user to pull key data manually from the Jellyfish UI and paste it in. Then analyze it.

Ask the user:
> "Please open your Jellyfish dashboard and paste in any of the following — I'll analyze what you share:
> - DORA scorecard (screenshot description or copy-paste)
> - PR cycle time breakdown (avg time in: coding, review, merge)
> - Team throughput (PRs merged / tickets closed per week)
> - AI tool usage stats (Cursor/Claude Code adoption %)
> - Delivery forecast for current sprint"

## Metrics interpretation guide

Once data is available (via API or manual), interpret and surface:

### DORA Metrics
| Metric | Elite | High | Medium | Low |
|---|---|---|---|---|
| Deployment frequency | Multiple/day | Daily | Weekly | Monthly |
| Lead time for change | <1 hr | <1 day | <1 week | >1 week |
| Change failure rate | <5% | <10% | <15% | >15% |
| MTTR | <1 hr | <1 day | <1 day | >1 week |

Flag which band the team is in and what's holding them back.

### PR Cycle Time Analysis
Break down where time is lost:
- **Coding time** — time from branch creation to first commit push
- **Review wait** — time from PR open to first review
- **Review time** — time from first review to approval
- **Merge wait** — time from approval to merge

If review wait > coding time → team has a review bottleneck.
If review time is high → PRs are too large or context is unclear.

### AI Tool ROI
Compare:
- PR merge rate: AI-assisted developers vs non-assisted
- Cycle time delta: before vs after AI tool adoption
- Code churn rate: higher churn may indicate AI-generated code needing more rework

### Sprint / Delivery Health
- Are epics on track per the Jellyfish forecast?
- Which tickets are at risk?
- Capacity utilization vs planned

## Output format

Produce a briefing the team can use in planning:

```markdown
# Jellyfish Engineering Briefing — <date>
**Team:** <team>  **Period:** <period>

## DORA Band: <Elite/High/Medium/Low>
- Deployment frequency: <value>
- Lead time: <value>
- Change failure rate: <value>
- MTTR: <value>

## PR Cycle Time
- Avg total: <X> hrs
- Bottleneck: <coding | review wait | review | merge>
- Recommendation: <specific action>

## AI Tool Impact
- Adoption: <X>% of team using <tool>
- Cycle time impact: <+/- X%>
- Recommendation: <specific action>

## Sprint Health
- On-track: <X of Y epics>
- At-risk: <list>

## Top 3 Recommendations
1. ...
2. ...
3. ...
```

## Integration with other skills

- Before `/architect-plan`: use Jellyfish capacity data to validate scope is feasible
- Before sprint planning: use delivery forecast to set realistic commitments
- After `/code-review`: correlate review findings with Jellyfish cycle time data
- After `/github-review-comments`: check if review bottleneck is a systemic Jellyfish-visible pattern

## Additional resources

- [Jellyfish DORA guide](https://jellyfish.co/blog/) — latest Jellyfish research and benchmarks
- Jellyfish AI Engineering Trends report: `jellyfish.co/ai-engineering-trends/`
