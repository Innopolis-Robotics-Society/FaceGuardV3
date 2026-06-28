## Learning points
The team learned that customer feedback must be converted into actionable PBIs with clear acceptance criteria. Writing quality requirements according to ISO/IEC 25010 taught us to use measurable scenarios instead of vague statements. QRTs must be automated to count as valid verification; tests with fake inputs pass locally but do not catch real hardware issues. The customer approved face registration, recognition, admin panel, and access logs during UAT, but performance issues on Raspberry Pi 5 remain the top concern.
## Validated assumptions
Face recognition pipeline logic works and was approved by the customer during UAT. The 3-second response time assumption was rejected — customer reports degraded speed and freezes on Raspberry Pi 5. CI configuration assumption was also rejected; the workflow is written but not triggered on the protected branch. Tests with fake inputs are insufficient for quality verification, as real hardware reveals issues not caught in the test environment.

## Friction and gaps
QR-001 (Time Behaviour) is not satisfied in production due to Raspberry Pi 5 performance limitations. QR-002 (Security) is not validated with real printed-photo attacks. CI workflow is blocked by repository permissions. Video-based registration and temporary access with start/end dates are customer-requested features not yet implemented.

## Planned response
Profile and optimize the recognition pipeline on Raspberry Pi 5, adjusting QR-001 if necessary. Configure GitHub Actions CI on the protected default branch and update Definition of Done to require CI pass. Implement video-based registration and date-range temporary access (FACE-62, FACE-63). Validate anti-spoofing with real printed-photo attacks (FACE-57) and improve UAT instructions with screenshots.

