ᅠ
# Sprint Review Summary — Sprint 4, Week 6

**Date:** 10.07.2026
**Format:** Offline, in person
**Participants:** Development team, Customer (role: admin)
**Recording:** The meeting was recorded with the customer's permission. A sanitized transcript was published, since the customer approved publication. UAT execution and the transition discussion were conducted during the same session, so this recording also covers both.

## Scope reviewed

Sprint 4, Week 6 Trial Release: MVP v2 progress (towards MVP v3).

## Artifacts demonstrated

- Admin login and authentication
- Employee registration, including temporary access with an expiration date
- Recognition threshold and embedding averaging, explained to the customer
- Employee deletion and sorting in the employee list
- Background recognition: the admin can navigate between pages while recognition keeps running
- Migration from the Streamlit admin panel to a separate frontend
- Migration of the database from cloud storage to fully local storage on the device

## Feedback

**Positive:**
- Employee deletion and list sorting work well
- Background recognition works: the admin can move between pages without interrupting recognition
- The customer confirmed the system works overall and expressed clear approval

**Minor issues raised (customer described these as minor, not blocking):**
- The camera stream occasionally does not capture properly on the board
- Loading can be slow on weaker hardware

**Explicit requirement stated by the customer:**
- No external databases and no cloud resources of any kind. All data must be stored locally on the device only. The customer stated this firmly after learning the team had previously used cloud storage before migrating to local storage.

**Requested improvements:**
- Add validation to the temporary access date and time field so past dates cannot be selected; the earliest allowed value should be the current date and time
- Add dedicated documentation describing the system's functions, for example a static documentation page or site

## Approvals and requested changes

The customer approved the current Sprint 4 progress and confirmed the system works. The customer did not confirm the current documentation as sufficient; instead, the customer requested additional documentation describing the system's functions.

## Risks

- If external or cloud storage is reintroduced by mistake in a future change, this would violate an explicit customer requirement
- If date validation is not added, the admin could set an invalid or past date for temporary access

## Resulting issues

- [#224](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/224)
- [#219](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/219)
- [#235](https://github.com/Innopolis-Robotics-Society/FaceGuardV3/issues/235)

## Action points

- Fix the occasional page freeze under load
- Add date and time validation for temporary access, minimum value is the current date and time
- Continue optimizing performance and stability on Raspberry Pi
- Clean up the repository and add a static documentation site describing the system's functions

## Note on scope

Physical door integration was not delivered and is not planned as a separate feature; the team clarified that the LED indicators serve as the visual signal in place of a physical door mechanism, and no further work on a physical door is planned.
