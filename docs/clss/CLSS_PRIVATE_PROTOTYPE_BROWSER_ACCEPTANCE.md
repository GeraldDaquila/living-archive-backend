# CLSS Private Prototype Browser Acceptance Plan

Status: test plan only. The current private WordPress prototype has not been changed by this document.

## Preconditions

- Work only on the private draft page (ID 79848) and its CLSS shortcode plugin.
- Take a recoverable backup/checkpoint before any eventual write.
- Keep the public page unpublished and the draft private.
- Use a complete reviewed plugin-file replacement, never a partial patch.
- Do not alter the CLSS Woody snippets, USE, The Guide, Render, or any production service.
- Keep answers in page memory only. No network request, API call, analytics event, or persistent save may carry answer text.

## Entry and perspective

1. The page shows two explicit choices: “Reflect on my own leadership” and “Reflect on another person's leadership.”
2. Neither choice is preselected in a way that silently chooses for the visitor.
3. Choosing self-reflection displays only self-framed prompts.
4. Choosing third-party reflection displays only third-party-framed prompts.
5. The selected perspective remains visible throughout questions and results.
6. Refresh/restart behavior is clear; the interface does not pretend that session-only answers survive a refresh.

## Question flow

7. Exactly nine question steps appear for the selected perspective.
8. The visitor can go back without losing already entered answers.
9. “Mark as unknown” preserves a blank answer and advances correctly.
10. Progress indicator and question count stay accurate.
11. Repeated shortcode or repeated initialization does not create duplicate handlers, duplicate IDs, or a second competing interface.
12. Every visible control is keyboard reachable and has a useful accessible name; focus moves sensibly after navigation.

## Result composition

13. The result states plainly that this is a reflection aid, not a score or verdict.
14. Entered answers are displayed accurately, escaped safely, and remain distinguishable from interpretation.
15. Blank answers are described as missing information, never negative evidence.
16. Self-reflection wording does not accidentally refer to the visitor as “this person.”
17. Third-party wording does not claim to know private motives or thoughts.
18. The summary distinguishes what was entered, what may be supported, what is interpretation, what remains unclear, and one proportionate next step.
19. Conflicting or insufficient information is not turned into a confident conclusion.
20. No hiring, promotion, removal, or suitability decision is generated.
21. A useful next resource appears only if the implementation can justify it from the entered answers; otherwise no resource is shown. No fixed resource list is forced into every result.
22. All resource links match the approved CLSS registry and open the intended destination.

## Privacy and resilience

23. With browser developer tools open, complete both perspectives and confirm that no answer text is sent in a network request.
24. Confirm there are no analytics or persistent-storage writes containing answers.
25. Empty answers and long-but-valid answers do not break the page.
26. Special characters and HTML-looking input are rendered as text, not executable markup.
27. Restart clears all answers and the prior result.
28. A failed script or unavailable optional feature does not present a fabricated interpretation.

## Print and layout

29. Print preview contains the current result only, not the surrounding website navigation or hidden question screens.
30. The print button is hidden in print output; printed text is readable in black and white.
31. Desktop and mobile widths have no horizontal overflow; focus areas and buttons remain usable.
32. No malformed action-container markup appears in the rendered DOM.

## Evidence record

For every test, record: test number, browser/device, pass/fail/not run, short observed result, and screenshot or console/network evidence where relevant.

**Release gate:** do not publish or expose the draft publicly until all applicable checks pass, defects are corrected, and the test record is reviewed. Passing GitHub unit tests is necessary but does not replace browser acceptance.
