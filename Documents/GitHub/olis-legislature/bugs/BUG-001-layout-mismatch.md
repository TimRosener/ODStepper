# BUG-001: Layout Mismatch - Sidebar CSS Not Used, Content Cramped

## REPORTED ISSUES
1. "Ton of gray at the bottom of the example template" - excessive gray/empty space
2. "All the items are shoved over towards the right" - content alignment issues  
3. Sidebar navigation visible in screenshot but not properly implemented

## ROOT CAUSE ANALYSIS
FILE: /Users/ianswanson/Development/starter-template/frontend/index.html
LINES: 14-112

CURRENT BEHAVIOR:
- HTML uses simple `.page-container` layout (line 14) 
- `.page-container` has `max-width: 800px` and `margin: 0 auto` (design-system.css line 289-293)
- This creates a narrow centered column, leaving wide gray margins
- Design system includes complete sidebar layout components (.app-layout, .sidebar, .main-content) in components.css but they are unused
- Results in cramped content pushed to center with excessive whitespace

EXPECTED BEHAVIOR:
- Should use sidebar layout components that exist in design system
- Content should fill available space properly
- Navigation should be in sidebar, main content in expanded area

## SPECIFIC CODE LOCATIONS

### Primary Issue - HTML Structure
FILE: /Users/ianswanson/Development/starter-template/frontend/index.html  
LINES: 14-112
PROBLEM: Uses `.page-container` instead of `.app-layout` structure

### Supporting CSS Evidence
FILE: /Users/ianswanson/Development/starter-template/shared/design-system.css
LINES: 289-293
DEFINES: `.page-container` with restrictive `max-width: 800px`

FILE: /Users/ianswanson/Development/starter-template/shared/components.css  
LINES: 391-483
DEFINES: Complete sidebar layout system (unused)

## MINIMAL FIX SCOPE
CHANGE ONLY: HTML structure in frontend/index.html lines 14-112
REPLACE: `.page-container` layout with `.app-layout` + `.sidebar` + `.main-content` structure
USE: Existing CSS classes from components.css - no new CSS needed

## DESIGN SYSTEM PRESERVATION
- MUST use existing `.app-layout`, `.sidebar`, `.main-content` classes from components.css
- MUST use existing `.sidebar-nav`, `.sidebar-link` classes for navigation
- MUST preserve all existing card, button, form components as-is
- MUST maintain color scheme and spacing using design system variables

## DO NOT TOUCH
- /Users/ianswanson/Development/starter-template/shared/design-system.css
- /Users/ianswanson/Development/starter-template/shared/components.css  
- /Users/ianswanson/Development/starter-template/frontend/style.css
- Any JavaScript functionality in app.js
- Any FastAPI backend code

## CONSTRAINT ENFORCEMENT
BUG SCOPE: Fix only HTML structure. Do not refactor CSS. Do not add features.
LESSON VIOLATION CHECK: Complies with Rule #1 (no design system modifications), Rule #3 (minimal bug fix scope)

## EXPECTED OUTCOME
- Sidebar navigation on left (~240px width)
- Main content area utilizing full remaining width
- Elimination of excessive gray margins
- Content properly distributed across screen width
- Consistent with design system's intended sidebar layout