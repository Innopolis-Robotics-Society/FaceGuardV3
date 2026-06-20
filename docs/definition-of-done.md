# Definition of Done

A Product Backlog Item (PBI) may be marked Done only when ALL of the following are satisfied:

- [ ] All issue-specific acceptance criteria are satisfied  
- [ ] The work is reviewed and approved by a different team member than the implementer  
- [ ] For user stories, all linked supporting PBIs provide the required  
      implementation, review, and verification evidence  
- [ ] Required automated tests and/or manual verification checks pass  
- [ ] For changes affecting the recognition pipeline (OpenCV/InsightFace), 
      manual verification on the test page is performed and recorded  
- [ ] If a Docker container is affected, the container builds and runs 
      successfully with the change included  
- [ ] No secrets, credentials, or real/non-sanitized employee data are 
      committed to the repository  
- [ ] Verification evidence is preserved in the normal workflow artifacts 
      (PR/MR description, linked issue, or reports/)  
- [ ] CHANGELOG.md is updated with a user-visible entry, or explicitly 
      marked not applicable  
- [ ] Relevant documentation (README, docs/) is updated if the change 
      affects setup, usage, or interfaces  
- [ ] For supporting or implementation PBIs, the issue-linked PR/MR is 
      merged into the protected default branch (`main`)
- [ ] CI checks (Lychee, tests) pass  
