---
name: create-skill
description: 'Create or refine a VS Code agent skill. Use when turning a conversation, repeatable workflow, checklist, or domain procedure into a workspace or personal SKILL.md with valid frontmatter, clear triggers, and testable completion criteria.'
argument-hint: 'Describe the workflow or outcome this skill should support.'
user-invocable: true
---

# Create an Agent Skill

Turn a repeatable workflow into a focused, discoverable `SKILL.md` that another agent can follow without relying on hidden conversation context.

## When to Use

- A user wants to create, refine, or review a `SKILL.md`.
- A conversation contains a reusable multi-step workflow, decision tree, checklist, or quality gate.
- A prompt, procedure, or set of coding habits should become an on-demand agent capability.

## Procedure

1. Review the conversation and any supplied files for the workflow being generalized. Extract:
   - the intended outcome;
   - ordered steps and decision points;
   - inputs, constraints, and required tools;
   - quality checks and the definition of done.
2. Determine scope before editing:
   - use `.github/skills/<name>/` for a project or team-shared skill;
   - use the user's supported personal skill location for a cross-workspace skill;
   - ask when scope is not inferable.
3. Confirm that a skill is the right primitive. Prefer instructions for behavior that applies broadly, a prompt for one focused task, and a custom agent when context isolation or distinct tool restrictions are required.
4. Choose a lowercase hyphenated name from 1 to 64 characters. Make it match the containing folder exactly.
5. Draft `SKILL.md` with YAML frontmatter containing `name` and a keyword-rich `description`. Add `argument-hint` only when an invocation benefits from user input. Keep the body under 500 lines and use relative `./` paths for bundled resources.
6. Write the body around the real workflow:
   - state what the skill accomplishes;
   - list concrete trigger conditions;
   - provide numbered, executable steps;
   - make branches and assumptions explicit;
   - end with validation and completion criteria.
7. Split large or optional material into nearby `references/`, `scripts/`, or `assets/` files. Link each resource from `SKILL.md` and load it progressively.
8. Validate the result:
   - the folder and `name` match;
   - frontmatter is between two `---` markers and uses spaces, not tabs;
   - `description` says both what the skill does and when to use it;
   - instructions are self-contained, actionable, and free of unexplained placeholders;
   - referenced files exist and links use relative paths;
   - the completion checks can distinguish a finished result from a draft.
9. Identify the least certain or most consequential assumption. Ask the user one concise question about it, then revise the skill if the answer changes scope, behavior, or validation.
10. Summarize what the finalized skill produces and provide a few example prompts that should trigger it. Suggest adjacent customizations only when they address a clear remaining need.

## Quality Bar

- Prefer the smallest workflow that reliably produces the intended outcome.
- Put discovery-critical keywords in `description`; do not hide all triggers in the body.
- Preserve user intent while removing conversation-specific details.
- Do not invent bundled resources merely to add structure.
- Treat invalid frontmatter, mismatched names, broken links, and missing completion checks as blocking defects.