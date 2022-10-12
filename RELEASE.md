Before you start, make yourself familiar with the [Semantic Versioning][1] and also have a look at [Gitflow Workflow][2]. Especially the section about **Release branches**.

## Release Workflow

If you plan on releasing a new version follow these steps:

1. Create a new branch off of `dev` called `release/<version_of_the_release>`.
2. On the new release branch you perform all release related tasks, such as bumping the version number in the `pyproject.toml`. No new features should be implemented on this branch, "only bug fixes, documentation generation, and other release-oriented tasks should go in this branch" (see the mentioned [page about Gitflow Workflow][2]).
3. Once ready, merge the release branch into `main` and tag the merge with the version number. Make sure that you actually create a merge commit by specifiying `--no-ff` if you use git on the command line.
4. Also merge the branch back into `dev`
5. Now you can delete the release branch.

## Release Checklist

- [ ] Bump the version number in `pyproject.toml`

[1]: https://semver.org/ "Semantic Versioning"
[2]: https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow "Gitflow Workflow"
