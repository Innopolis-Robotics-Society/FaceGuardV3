# Reflection — Week 6 (Sprint 4)

## Learning points

This week confirmed that regular, focused customer touchpoints are essential for keeping the project aligned with real needs. Conducting the Sprint Review in person with the customer, demonstrating the system, and letting the customer interact with the interface provided much clearer feedback than written reports alone.

From the technical side, the most important lesson was that performance on edge hardware (Raspberry Pi) cannot be taken for granted. Even though the system worked well on laptops, the same code ran noticeably slower on the target device. Migrating the database from cloud storage to fully local storage was a necessary step.

Another important learning was the value of background processing. The team implemented background recognition, allowing the admin to navigate between pages while recognition continues to run. This was demonstrated during the Sprint Review and confirmed by the customer as working correctly.

## Validated assumptions

The assumption that the customer values privacy and local control over convenience was strongly validated. The customer firmly rejected any form of cloud or external database storage.

The assumption that performance would be the main concern was also validated. The customer confirmed the system works, but noted that speed could be improved. However, the customer described this as a minor issue rather than a critical blocker.

The assumption that documentation matters to the customer was validated. The customer explicitly requested additional documentation.

## Friction and gaps

The customer requested a dedicated page describing system functions, which was not yet available. This will be addressed in Sprint 5.

Another friction point was the occasional page freeze during recognition.

Date validation for temporary access was also identified as a missing feature. The customer requested that past dates should not be selectable, and the team committed to adding this validation in Sprint 5.

## Planned response

Based on the Sprint Review and customer feedback, the following actions are planned for Sprint 5:

1. Fix the occasional page freeze under load
2. Add date and time validation for temporary access, with the minimum value set to the current date and time
3. Continue optimizing performance and stability on Raspberry Pi
4. Clean up the repository and add a static documentation site describing the system's functions, as requested by the customer

The team will also complete the product handover, confirm the final transition status with the customer, and prepare for Demo Day.
