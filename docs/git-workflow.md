# Git and pull requests: team guide

Use this workflow for implementation tasks in this repository:

**Issue → branch → changes and checks → commits → push → pull request → review → merge.**

**Team execution rule:** follow the [parallel-work protocol](../tasks/parallel-work.md).
Keep one active implementation task per person. Independent lanes can run together
once their own prerequisites are verified and merged. Reserve shared-file edits
with the integrator; hand off dependency contracts at each merge. Task numbers and
lane labels alone do not determine readiness.

## 1. What each part means

| Term | Meaning |
|---|---|
| Repository (repo) | The project files and their change history. |
| Clone | Your local copy of the GitHub repository. |
| `main` | The shared, integrated version of the project. |
| Branch | A separate line of work where you implement one task. |
| Commit | A named snapshot of selected changes in your local branch. |
| Push | Upload your local commits to GitHub. |
| Pull | Bring remote changes into your local branch. |
| Issue | The task: owner, prerequisites, acceptance criteria and verification. |
| Pull request (PR) | A request to review and merge a branch into `main`. |
| Merge | Integrate the reviewed changes into the target branch. |

A commit does not upload anything. A push does not merge your work into `main`.
Opening a PR does not mean the task is complete.

## 2. One-time setup

Install Git, accept the repository invitation, and sign in to GitHub. Configure
the name and email used on your commits (use your GitHub no-reply email if desired):

```sh
git config --global user.name "Your Name"
git config --global user.email "YOUR_GITHUB_EMAIL"
git clone https://github.com/MoriondoTommaso/movie_ticketing_system.git
cd movie_ticketing_system
```

If you already have a clone, use that folder instead of cloning again.
For HTTPS authentication, use your credential manager or GitHub CLI's
`gh auth login`; your GitHub account password is not a Git password.
The `gh` commands below are optional: all PR actions also work on the website.

## 3. Start one assigned task

Read your issue, its prerequisites and the [assignment plan](../tasks/assignments.md).
Start when your task's required contracts/dependencies are verified and merged.
Do not wait for another person's whole lane to finish. Coordinate edits
to shared files with their integrator before coding.

Check that your working tree is clean, update `main`, then create a branch:

```sh
git status
git switch main
git pull --ff-only origin main
git switch -c feat/t05-ticket-pricing
```

This example is T05, GitHub issue **#6**. Substitute your own task ID and topic.
Use `feat/` for features, `fix/` for fixes, and `docs/` for documentation.
Keep one focused task per branch/PR; do not commit implementation directly to
`main`. If `git status` shows unfinished changes, commit them on their current
task branch before switching; do not discard them to make these commands work.
If `pull --ff-only` fails, ask for help reconciling the local commits rather than
resetting or force-pushing.

## 4. Make changes, verify, and commit

Implement the issue's acceptance criteria, including its tests. Run the focused
verification specified in the issue and inspect exactly what you will commit:

```sh
git diff
git diff --check
git status --short
git add src/pricing.py tests/unit/test_pricing.py
git diff --cached
git diff --cached --check
git commit -m "feat: implement ticket pricing (T05)"
```

The paths are examples for T05; stage your own task's files explicitly.
Never include `.env`, real credentials, personal data or unrelated changes.
Use clear messages such as `fix: release booking locks after failure` or
`docs: explain fresh database setup`.

Record actual verification commands and results. The project is currently a
scaffold: pytest/Ruff/MySQL commands become usable as their prerequisite tasks
land. A missing tool or test is not a passing check. Use the
[verification contract](../tasks/plan.md#verification-command-contract).

## 5. Push and open a pull request

```sh
git push -u origin feat/t05-ticket-pricing
```

On GitHub, open **Pull requests → New pull request** (or **Compare & pull
request**). Select **base: `main`** and **compare: your task branch**.
Review the Files changed tab for accidental files.

Use a title such as `T05: implement ticket pricing` and this description:

```markdown
## Summary
- What changed and why

## Issue
Closes #6

## Verification
- Command: ...
- Result: ...
- Manual evidence, if required: ...

## Coordination
- Shared files/contracts affected: ...
- Remaining blockers: none / describe them
```

Use the **GitHub issue number**, not the task number: T05 is #6, not #5.
`Closes #6` closes the issue when the PR merges into the default branch. Use
`Refs #6` for partial work that must leave the issue open.
Open a **Draft PR** for early feedback or blocked/incomplete work; mark it
**Ready for review** when the task and its checks are complete.

Optional CLI equivalent (opens a browser to finish the PR):

```sh
gh pr create --base main --head feat/t05-ticket-pricing --web
```

## 6. Request review and respond

- **Alessandro, Deniz and Eleonora:** request `MoriondoTommaso`.
- **Tommaso and Bianca:** request `eleonoraraimondo-hub`.
- Do not approve your own work.
- Eleonora also helps Tommaso prepare evidence and triage reviews.

Select the reviewer in the PR sidebar. If reviewer assignment is unavailable,
mention the reviewer in a comment and ask them to review.
An issue assignee is the implementer; a PR reviewer checks the work.

Reviewers inspect correctness, acceptance evidence, tests, shared contracts and
unrelated changes. They submit **Approve**, **Request changes**, or **Comment**.
For requested changes, edit on the same branch, rerun affected checks, commit,
and push again:

```sh
git add src/pricing.py tests/unit/test_pricing.py
git commit -m "fix: cover pricing anniversary boundary"
git push
```

The existing PR updates automatically. Reply to feedback and request re-review;
do not open another PR for each correction. Approval applies to reviewed code:
substantive changes after approval need another look.

## 7. Update your branch and handle conflicts

When shared code changes or GitHub says the branch conflicts, save your work in
a commit first, then merge the latest `main` into your task branch:

```sh
git fetch origin
git switch feat/t05-ticket-pricing
git merge origin/main
```

If Git reports conflicts:

1. Run `git status` to see the conflicted files.
2. Open each file and find `<<<<<<<`, `=======`, and `>>>>>>>` markers.
3. Combine the intended changes with the other owner; do not blindly choose
   "ours" or "theirs". Remove the markers after resolving the content.
4. Stage resolved files, complete the merge, rerun affected checks and push:

```sh
git add path/to/resolved-file
git commit
git diff --check
# Run the affected task's verification commands here.
git push
```

If unsure, `git merge --abort` cancels the in-progress merge so you can ask for
help. Start merges with a clean working tree. Avoid force pushes on shared
branches; this merge-based workflow does not require them.

## 8. Merge and finish

Before merging, confirm:

- The named reviewer approved and requested changes are addressed.
- All acceptance criteria and required verification pass; any configured GitHub
  checks pass too. No configured checks does not mean tests ran.
- Dependencies are integrated and conflicts resolved.
- The PR includes task evidence and updates the corresponding completed task
  and acceptance checkboxes in `tasks/todo.md`. Review approval completes that
  status update; merging the PR publishes it alongside the implementation.

Tommaso or Eleonora can merge reviewed PRs after required checks pass. Neither
self-approves; use the review routing above, including shared-file reviews.
Choose **Squash and merge** when available to keep one task-level commit on
`main`; retain the task ID in its title. Delete the merged remote branch using
GitHub's **Delete branch** button. These are team conventions, not a claim that
branch protections or automatic CI are already configured.

Refresh your local copy after merge:

```sh
git switch main
git pull --ff-only origin main
git fetch --prune
git branch -d feat/t05-ticket-pricing
```

After squash merging, `git branch -d` may refuse because the original commits
were replaced by one new commit. Leave the branch until you verify that GitHub
shows the PR as merged, `main` contains the work, and the branch has no unmerged
follow-up changes. Only then use `git branch -D feat/t05-ticket-pricing` to remove
that local branch. Start the next task from updated `main`, not the old branch.

Confirm the linked issue closed; if it is still open, check why and close it only
when all acceptance criteria are satisfied. A task merge does not automatically
complete its checkpoint: C01–C10 require their own integration evidence.

## Quick daily checklist

1. Pick your next ready task, check merged dependencies, and reserve shared files.
2. Update `main`; create a focused task branch.
3. Implement, test, inspect changes, commit and push.
4. Open a linked PR and request the named reviewer.
5. Address feedback on the same branch and rerun affected checks.
6. Merge after approval and verification; update local `main`.

For Deniz: accept the pending repository invitation before pushing. His reserved
issues and the commands to finish their GitHub assignment are in the
[assignment plan](../tasks/assignments.md#pending-invitation).
