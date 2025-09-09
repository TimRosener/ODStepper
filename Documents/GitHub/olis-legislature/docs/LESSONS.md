# Lessons Learned - Never Again Rules for AI Agent Company Template

This file contains specific rules learned from past failures to prevent them from happening again within the AI Agent Company starter template system.

## Rule #1: No design system modifications without explicit human request
**Context**: AI tends to modify /shared/design-system.css and /shared/components.css files
**Why it failed**: Breaks consistency across all applications using the template
**Rule**: Never modify files in /shared/ directory. Use existing CSS variables and components only.
**Applies to**: Builder, Architecture Guardian

## Rule #2: One story at a time, no exceptions
**Context**: Teams tend to work on multiple features simultaneously, leading to incomplete releases
**Why it failed**: Context switching prevents completion and creates integration issues
**Rule**: Only ONE story can be in "in_progress" status at any time. Complete before starting next.
**Applies to**: Product Scope, Builder

## Rule #3: No "quick improvements" during bug fixes
**Context**: Developers see bugs as opportunities to "improve" surrounding code
**Why it failed**: Introduces new bugs and makes testing unpredictable within template system
**Rule**: Bug fixes must change ONLY the specific lines causing the reported issue
**Applies to**: Builder, Bug Translator

## Rule #4: Never use inline styles or custom CSS
**Context**: AI creates custom styles instead of using design system variables
**Why it failed**: Breaks visual consistency and makes template unmaintainable
**Rule**: Use ONLY CSS variables from design-system.css (--primary, --space-md, etc)
**Applies to**: Builder

## Rule #5: Follow single-server architecture
**Context**: AI tries to create separate backend/frontend servers
**Why it failed**: Breaks template's simple deployment model and ./start.sh script
**Rule**: FastAPI serves both API (/api/*) and frontend (/). No separate servers.
**Applies to**: Architecture Guardian, Builder

## Rule #6: Always use Bug Translator for human-reported issues
**Context**: Human reports UI problems, AI immediately starts coding fixes
**Why it failed**: Bypasses bug analysis process, leads to over-fixing and scope violations
**Rule**: When human reports bugs, MUST activate Bug Translator first to create ticket in /bugs/
**Applies to**: All agents responding to human QA feedback

---

*Process Observer will add new lessons here as failures are reported and analyzed.*