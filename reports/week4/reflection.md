## Learning points
The team learned that customer feedback must be converted into actionable PBIs with clear acceptance criteria. Writing quality requirements according to ISO/IEC 25010 taught us to use measurable scenarios instead of vague statements. QRTs must be automated to count as valid verification; tests with fake inputs pass locally but do not catch real hardware issues. The customer approved face registration, recognition, admin panel, and access logs during UAT, but performance issues on Raspberry Pi 5 remain the top concern.

## Validated assumptions
Face recognition pipeline logic works and was approved by the customer during UAT. The 3-second response time assumption was rejected, as customer reports degraded speed and freezes on Raspberry Pi 5. CI pipeline was successfully configured and all 28 tests pass on the protected default branch. Tests with fake inputs are insufficient for quality verification, as real hardware reveals issues not caught in the test environment.

## Friction and gaps
QR-001 (Time Behaviour) is not satisfied in production due to Raspberry Pi 5 performance limitations. QR-002 (Security) is not validated with real printed-photo attacks.

## Planned response
Profile and optimize the recognition pipeline on Raspberry Pi 5, adjusting QR-001 if necessary. Implement duplicate name check [#115](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/115), time-based temporary access [#117](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/117), employee editing [#113](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/113), last entry timestamp [#114](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/114), and log date filtering [#116](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/116) based on UAT feedback. Validate anti-spoofing with real printed-photo attacks and improve UAT instructions with screenshots.
