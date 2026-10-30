"""The four cells a candidate-against-environment run can land in.

A cell names what the run established, not whether that is good news. A
candidate that stays silent against the real app is doing its job. The same
silence against a broken copy is the defect the gate exists to catch. Which
cell belongs where is the gate's business, not the cell's.

Two cells are not enough, and that was measured elsewhere before it was
written here. A candidate that asserts nothing passes everything, so folding
vacuous into silent loses the one distinction that tells a useless test from a
weak one. did-not-run is separate for the same reason: a run that never
reached a verdict is not a pass.
"""

CATCHES = "catches"
SILENT = "silent"
VACUOUS = "vacuous"
DID_NOT_RUN = "did-not-run"

CELLS = (CATCHES, SILENT, VACUOUS, DID_NOT_RUN)

PASS = "pass"
FAIL = "FAIL"
ERROR = "error"
