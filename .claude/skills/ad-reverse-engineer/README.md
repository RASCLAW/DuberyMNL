# ad-reverse-engineer

## What it is
A general-purpose skill for reverse-engineering any ad image into a production-ready NB2 prompt. Based on the methodology Gemini used to deconstruct RA's original DuberyMNL infographic ad.

## When to use
- You have a reference ad you like and want to replicate the format for a new product/caption
- You want to extract the "design DNA" of an existing ad before building a new template
- You're building a new content type and need to formalize its visual rules

## The Method (4 Layers)
Gemini's breakdown — now saved as our own:

1. **Backdrop** — Where is this? What's the environment, light, surface?
2. **Hero** — What is the main subject? How is it positioned, lit, styled?
3. **Graphics** — What design elements sit on top? Shapes, lines, arrows, badges?
4. **Text** — What text exists? Font weight, capitalization, position, hierarchy?

Then extract the **design rules** the creator was following:
- Layout logic (Rule of Three, golden ratio, Z-pattern, etc.)
- Hierarchy (what's big vs. small, bold vs. regular)
- Contrast technique (what makes the hero pop)
- Accent elements (what draws attention to key areas)

## Input
An image file path or URL of the reference ad.

## Output
1. A structured layer breakdown of the ad (Layers 1-4 + design rules)
2. A production-ready NB2 JSON prompt with variable placeholders marked for substitution

## Related
- `dubery-infographic-ad` — the DuberyMNL template produced by applying this method
- `dubery-prompt-writer` — full WF2 prompt writer for all content types
- `nano-banana-2` — NB2 schema reference
