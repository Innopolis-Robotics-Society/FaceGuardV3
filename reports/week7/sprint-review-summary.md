# Sprint Review Summary — Sprint 5, Week 7

**Date:** 16.07.2026   
**Format:** Offline, in person  
**Participants:** Development team, Customer (role: admin)  
**Recording:** The meeting was recorded with the customer's permission. A sanitized transcript was published, since the customer approved publication. UAT execution and the final transition confirmation were conducted during the same session, so this recording also covers both.  

## Scope reviewed

Sprint 5, Week 7: final MVP v3 release.

## Artifacts demonstrated

- Admin login and password management, including generating a new password hash and changing login credentials at any time
- Login lockout after 5 failed attempts within one minute
- Employee registration with permanent access
- Temporary access with future-only date and time validation
- Recognition quality guidance
- Recognition with accessories: glasses recognized correctly, masks intentionally rejected
- Anti-spoofing: a photograph presented to the camera instead of a real face was rejected
- Employee list, including sorting, search, activity logs, deleting, and last access time
- Hosted documentation site, covering authentication, registration, recognition status colors, deployment steps, and how to generate password hashes, in light and dark themes
- Performance improvements on Raspberry Pi (optimized as much as possible within hardware limitations) and reduction of the registration black-screen issue
- Logs list
- Customer confirmation of independent system operation, transition readiness, and final product acceptance

## Feedback

**Positive:**
- Password hashing and login management approved.
- Login lockout demonstrated and confirmed working
- Temporary access date and time validation confirmed working, past dates are rejected
- Documentation reviewed live and no further changes requested
- The customer confirmed the system works and accepted it as the final delivered product

**Minor issues raised:** None raised this session.

**Requested improvements:** None.  

## Final transition confirmation

The customer was asked directly and answered:

- Able to use the system independently, without the team's assistance: **Yes**
- System already deployed in the customer's own environment: **Not yet**
- Current version sufficient to manage the system independently going forward: **Yes**
- Anything preventing the customer from taking full control now: **No**
- Accepts this as the final delivered product: **Yes**

## Approvals and requested changes

The customer approved the final Sprint 5 delivery as complete and accepted it as the final delivered product. No further changes were requested. Documentation was explicitly confirmed as sufficient.

## Risks

- The system has not yet been deployed on the customer's own infrastructure; this remains unconfirmed in a real deployment environment outside the demo setup

## Resulting issues

None. No new issues resulted from this session.

## Action points

None from the customer side. Remaining work is limited to final course wrap-up: Demo Day preparation and closing out any internal follow-up items already tracked from Week 6.

## Note on scope

Medical masks are intentionally not supported as a recognized accessory. The team explained that a mask significantly distorts the facial embedding, which would reduce the reliability of the identity match, so recognition attempts made while wearing one are deliberately rejected. This is a security and reliability decision, not a defect, and no further work on mask support is planned.
