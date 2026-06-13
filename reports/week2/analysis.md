## Learning points
We realized that the camera interface prototype helped identify confusion with the recognition status indication. MVP v0 showed that snapshot delay is critical and requires optimization before finalizing all user scenarios. We also learned that the customer does not have a UPS, so the camera also stops working during a power outage.

## Validated assumptions
We assumed the system does not need to recognize faces in a crowd, just one person in front of the camera — confirmed during the customer meeting.
We assumed LED indication of access statuses could be implemented — confirmed during the technical feasibility discussion.
We assumed the accuracy of the off‑the‑shelf recognition model would be sufficient for real‑world conditions — rejected after MVP v0 testing in low light.

## Needs clarification
It remains unclear how the LEDs will be connected to visualize the verification status.

## Planned response
We will refine the camera interface for clear status display (US-012). We will replace the model with one more robust to low‑light conditions.