# Reflection — Week 7 (Sprint 5)

## Learning points

This week showed the value of asking direct, unambiguous questions when confirming a final outcome. Instead of relying on general impressions, the team asked the customer explicit yes/no questions about independent use, deployment status, documentation sufficiency, and final acceptance. This produced a clear, traceable record of the transition outcome rather than a vague sense that "things went well."

The team also learned that closing out feedback from a previous session is not just about fixing the underlying issue, it is about proving the fix to the customer directly. Re-demonstrating the temporary access date validation and re-running the affected UAT scenario, rather than just stating it was fixed, is what actually closed the loop with the customer.

Another learning point was about communicating deliberate design trade-offs. The decision to reject recognition attempts made while wearing a medical mask was explained clearly, with the underlying reason (embedding distortion, reliability, security), and the customer accepted it without concern. Being upfront about a limitation, and framing it as an intentional decision rather than leaving it undocumented, avoided confusion.

Finally, the team confirmed that hardware constraints on the Raspberry Pi are a hard limit, not something that can be fully engineered away in the time available. Registration and recognition remain measurably slower on the target device than on a laptop, even after optimization. Recognizing this limit early helped set realistic expectations with the customer instead of promising further speed improvements that hardware could not support.

## Validated assumptions

The assumption that fixing the three items raised in Week 6, the occasional page freeze, missing date validation, and missing function-description documentation, would be sufficient for the customer to accept the product was validated. When asked directly if anything else needed to be added or changed, the customer answered that everything was as expected.

The assumption that the customer would accept a security-motivated limitation, such as excluding masks from supported accessories, as long as it was clearly explained, was also validated. There was no pushback once the reasoning was given.

The assumption that hardware performance would remain a constraint rather than a fully solvable problem was validated as well. The team optimized as much as practical within the limitations of the Raspberry Pi, and the customer accepted this as sufficient rather than expecting further improvement.

## Friction and gaps

The main remaining gap is that the system has not yet been deployed on the customer's own infrastructure. The customer confirmed the current version is sufficient to do this independently, but as of the Week 7 session it had not yet happened. This is expected to occur after the course concludes and is outside the team's direct control.

A smaller friction point was scope drift in the accessory requirement: masks were originally listed as a supported accessory in the UAT scenario, and only during this sprint was it clarified and documented that mask support is intentionally excluded. Catching this kind of drift between the original requirement and the delivered behavior earlier would have avoided last-minute updates to the UAT documentation.

## Planned response

With the Sprint Review confirming full customer acceptance and no further requested changes, the remaining work is focused on course wrap-up rather than new product development:

1. Finalize the MVP v3 release and confirm the repository, documentation, and hosted documentation site remain accessible after the course ends
2. Prepare and rehearse the Demo Day presentation
3. Keep the customer informed of any final housekeeping needed before independent deployment on their own infrastructure
4. Preserve all Week 6 and Week 7 evidence, including transcripts, UAT results, and the customer handover document, in their final state for grading
