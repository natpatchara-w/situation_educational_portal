---
name: volunteer-checklist-creator
description: Create practical preparation documents and checklists for student volunteers organizing community events. Use when Codex is asked to read an event page, press release, article, brief, agenda, or notes and produce a volunteer-facing preparation guide covering things to bring, documents to read, roles, schedule, transport, safety, conduct, facilitation, documentation, and day-of checklists.
---

# Volunteer Event Prep

## Purpose

Use this skill to turn an event source into a clear preparation document for volunteers. Favor practical readiness over generic summaries: volunteers should know what to read, what to pack, where to go, how to behave, and what to confirm before the event.

## Workflow

1. Gather the event source.
   - If the user gives a URL and asks to read it, browse or fetch the page before drafting.
   - If the source is a local file, read it directly.
   - If the source is incomplete, make conservative assumptions and mark items as "confirm with organizer."

2. Extract operational facts.
   - Event name, organizer, purpose, audience, date, time, duration, location, and source URL or file.
   - Partners, local contacts, speakers, facilitators, and volunteer groups.
   - Activities, learning objectives, materials, expected participants, and safety context.
   - Any mismatch between URL/title/body/date should be noted briefly.

3. Create a volunteer-facing document.
   - Write in clear Markdown unless the user requests another format.
   - Include source attribution near the top.
   - Use specific details from the source, but do not invent unverified logistics.
   - Add "confirm" language for dates, meeting points, transport, participant count, or contacts that are not explicit.
   - Keep tone direct, respectful, and useful for a student volunteer team.

4. Include these sections when relevant.
   - Event summary
   - Locations and schedule to confirm
   - Transportation mode and travel preparation
   - Volunteer goals
   - Documents/materials to read before the event
   - Key messages volunteers should understand
   - Things to bring
   - Preparation timeline
   - Suggested volunteer roles
   - Sample run-of-show
   - Conduct guidelines
   - Quick checklist

5. Save or package the output if requested.
   - If the user asks for a file, save it in the workspace with a descriptive filename.
   - If a previous packaged copy exists, refresh it only when useful.
   - Verify generated archives with `unzip -t` when creating or updating a zip.

## Transportation Guidance

Always consider transport for community events, especially when locations are remote, multi-site, or require carrying materials.

Prefer coordinated group transport such as organizer vehicle, van, minibus, or car convoy. Include:

- meeting point and departure time
- transport lead
- driver contact and vehicle plate number
- passenger list
- route and backup route
- last-mile plan
- return pickup or waiting plan
- emergency cash
- safety rules such as seatbelts, helmet use for approved motorcycle rides, traveling in pairs, and offline maps

If transport details are absent from the source, state the recommended mode and add checklist items to confirm final arrangements.

## Useful Template

Use `assets/volunteer_event_preparation_template.md` as a starting point when creating a new Markdown document. Copy it into the workspace and replace bracketed placeholders with source-specific details.

## Quality Bar

Before finalizing:

- Check that every source-specific fact is either supported by the source or marked for confirmation.
- Ensure the checklist has actionable items, not vague reminders.
- Include child-safety, consent, and documentation guidance when the event involves children or community members.
- Include cleanup, follow-up notes, and photo/video backup after the event.
- Keep the final answer short and link the created file path.
