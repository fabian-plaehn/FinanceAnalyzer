**Small Business Tax Helper App – Concept Summary**
we will use python with pyside6 and uv

1. Purpose
A local, offline GUI application to help small businesses (initially your mom’s farm) prepare financial data for taxes by:
Importing bank statements (CSV)
Adding cash/manual entries
Automatically categorizing entries using flexible rules
Allowing easy manual review and correction
Producing clean, grouped Excel exports
This app does not calculate taxes, only prepares and structures data.

2. Users & Profiles
Single-user app (no logins)
Supports multiple business profiles
Each profile has its own:
Entries
Categories
Rules
Designed for non-technical users

3. Data Model (Core Entities)
Transaction Entry
Each entry contains:
Date
Amount (positive or negative)
Description (bank statement text)
Source (Bank A, Bank B, Cash)
Category (optional)
Flag: manual category (prevents auto overwrite)
Category
Flat list (no hierarchy)
Reusable across years
User-defined names
Rule
Maps entry → category
Types:
“Text contains X”
Regular expression match

Properties:
Target category
Enabled/disabled

Behavior:
Applies to existing and future entries
Does not overwrite manually categorized entries
Manual categories can optionally be unset to allow reprocessing

4. CSV Import System
Goals
Support multiple banks
Be highly customizable
Remain easy for non-technical users
Behavior
Import CSV files
User maps CSV columns to:
Date
Amount
Description
Mapping is saved per bank/profile
Handles:
Different column names
Different date formats
Detects duplicate entries to prevent double import
5. Manual (Cash) Entries
Added via simple form
Category can be set immediately
Treated the same as bank entries afterward
Manual entries can still appear in tables and exports
6. Categorization Flow
Automatic
Rules are applied automatically
Can be reapplied retroactively
Manual Review Required When:
No rule matches → Uncategorized
Multiple rules match → Rule Conflict
Manual Actions
User can:
Assign a category
Optionally later remove manual assignment to reapply rules
7. Main UI Structure (Tabs)
-Dashboard
Table view grouped by Category
Shows:
Individual entries
Category sums
Time filtering:
Custom date range
Table-focused, minimal charts (if any)
-Uncategorized
Table of entries not covered by any rule
Easy category assignment
-Multiple Rules Matched
Table of entries with conflicting rules
User selects correct category manually (The user should be able to do this everywhere and it should be very smooth)
-All Entries
Full table of all entries
Filters:
Date range
Category
Source
Manual category override possible here
8. Excel Export
Export Rules
Based on current dashboard filter
Uncategorized entries are ignored
Structure:
Grouped by category
Each category:
Table of entries
Category sum
Optional grand total
Output is “accountant-friendly”
9. Persistence & Safety
All data stored locally
Data persists across app restarts
Profiles stored independently
(Future) Optional backups / export of full project
10. Explicitly Out of Scope (for now)
Tax calculation
VAT handling
Multi-user accounts
Category hierarchies
Rule priorities (possible future enhancement)
11. Future Enhancements (Optional)
Rule priority ordering
Rule suggestions based on manual categorization
Category usage analytics
Simple visual charts
Receipt attachments
Year-based views