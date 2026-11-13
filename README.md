# NIST CSF 2.0 Control Mapping

A small Python tool that maps NIST Cybersecurity Framework 2.0 subcategories to the requirements of four other frameworks and regulations commonly seen in financial services GRC work.



**Anchor:** NIST CSF 2.0 (each row's ID is a CSF subcategory, such as 'PR.AA-03').

**Compared against:** SOC 2 TSC, GLBA Safeguards Rule, FFIEC IT Examination Handbook, ISO/IEC 27001:2022.





## Why CSF is the anchor



CSF is outcome-based and not prescriptive, which makes it a good common language. The other frameworks are each organized differently, so mapping them to a shared set of CSF outcomes shows where one control satisfies several obligations.





## What each column actually contains



These sources are not the same kind of thing, so the columns are not interchangeable.

|Column|What it holds|Notes|
|-|-|-|
|SOC 2 TSC|Criterion IDs such as 'CC6.1', 'A1.2', 'C1.1'|An attestation framework. Criteria are principles, and your own system description decides what is tested.|
|GLBA|Paragraph references to 16 CFR 314.4, such as '314.4(c)(5)'|This is the FTC Safeguards Rule, which covers non-bank financial institutions. Banks follow the Interagency Guidelines Establishing Information Security Standards instead, so paragraph numbers will not match.|
|FFIEC|Booklet-level references to the IT Examination Handbook|Booklet level only, not section level. See the key below.|
|ISO 27001|Annex A controls ('A.8.5') and management-system clauses ('6.1.2')|Clause numbers have no 'A.' prefix.|

### 

### 

### FFIEC key



|Tag|Source|
|-|-|
|InfoSec|Information Security booklet|
|AIO|Architecture, Infrastructure, and Operations booklet|
|BCM|Business Continuity Management booklet|
|DA\&M|Development, Acquisition, and Maintenance booklet|
|OTS|Outsourcing Technology Services booklet|
|Management|Management booklet|
|Audit|Audit booklet|
|Auth\&Access (2021)|FFIEC guidance on authentication and access to financial institution services and systems|
|TPRM guidance (2023)|Interagency Guidance on Third-Party Relationships: Risk Management|

\*\*The FFIEC Cybersecurity Assessment Tool (CAT) was sunset on August 31, 2025, so this tool does not map to it. Institutions have adopted frameworks such as NIST CSF 2.0 in its place, which is part of why CSF is a sensible anchor here.





## Quick start



Requires Python 3.8+ and no third-party packages.

'''bash
# Full-text search (any ID, theme, or description text)
python3 controlmap.py search "segregation"

# Show one CSF subcategory
python3 controlmap.py show PR.AA-03

# Reverse lookup: which CSF subcategories reference a control in another framework?
python3 controlmap.py lookup glba "314.4(c)(5)"
python3 controlmap.py lookup iso\_27001\_2022 A.8.13
python3 controlmap.py lookup soc2\_tsc CC7.2

# Look up a whole CSF category
python3 controlmap.py lookup nist\_csf\_2 PR.AA

# Gap view: which CSF rows have no mapping in a framework?
python3 controlmap.py coverage
python3 controlmap.py coverage glba ffiec

# Generate the searchable web page, or export JSON
python3 controlmap.py html -o index.html
python3 controlmap.py export -o controls.json
'''

Framework keys: 'nist\_csf\_2', 'soc2\_tsc', 'glba', 'ffiec', 'iso\_27001\_2022'.





## Verification status



* **GLBA paragraph references** were checked against the text of 16 CFR 314.4 (elements (a) through (j)).
* **FFIEC CAT sunset date** was checked against a published industry summary.
* **Everything else** (CSF subcategory titles, SOC 2 criteria, ISO Annex A mappings, FFIEC booklet assignments) was drafted from general knowledge and has **not** been verified line by line. Check it against NIST's CSF 2.0 reference tool, the ISO 27001:2022 Annex A list, the AICPA Trust Services Criteria, and the FFIEC IT Handbook before relying on it.





## Limitations



* Mappings are conceptual. Partial overlap is normal, and a listed ID does not mean full equivalence.
* This is a starter set of 57 CSF subcategories out of 106, with emphasis on the controls that matter most in financial services. Rows for several categories are not included yet.
* GLBA and banking-agency incident notification rules have their own timelines and thresholds. The notes column mentions some, but this tool is not legal advice.





## Extending it



* Add rows to 'controls.csv'. The CLI and the HTML page pick them up automatically.
* Add a framework by adding a column and one entry in the 'FRAMEWORKS' dict in 'controlmap.py' (candidates: PCI DSS 4.0, NYDFS 23 NYCRR 500, NIST SP 800-53).
* Add a mapping-strength column (full or partial), and a test that checks every ID against a list of valid IDs.





## Project layout



\~\~
controlmap.py   CLI and HTML generator
controls.csv    the mapping data (one row per CSF subcategory)
index.html      generated page (rebuild with the html command)
controls.json   generated export
\~\~

