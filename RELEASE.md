Before you start, make yourself familiar with the [Semantic Versioning][semver] and also have a look at [Gitflow Workflow][gitflow]. Especially the section about **Release branches**.

## Release Workflow

If you plan on releasing a new version follow these steps:

1. Create a new branch off of `dev` called `release/<version_of_the_release>`.
2. On the new release branch you perform all release related tasks. No new features should be implemented on this branch, "only bug fixes, documentation generation, and other release-oriented tasks should go in this branch" (see the mentioned [page about Gitflow Workflow][2]). Also have a look at the [Release Checklist](#release-checklist).
3. Once ready, merge the release branch into `main`. Also merge the release branch back into `dev`.
4. Afterwards run `cz bump` (or `make bump`) **on the `master` branch** to bump the version number, update the changelog and create a version tag automatically.
5. Now you can delete the release branch. The GitLab CI/CD should take care of compiling and uploading the package to PyPI/TestPyPI.

### Alpha and beta versions

Alpha and beta versions life on `dev` and `release/*` respectively. If you want to publish a pre-release, follow step 4 above and add `--prerelease [alpha,beta]` to the `cz` command (or run `make bump-alpha`/`make bump-beta`).

## Notes

The CI/CD pipeline needs API keys to be able to upload the compiled package to PyPI/TestPyPI. These API keys can be changed/added under *Settings -> CI/CD -> Variables*. Currently we have the following variables defined:

- `SCIEBO_KEY`: If you share a folder in sciebo you get a URL similar to `<sciebo server url>/index.php/s/<sciebo key>`. The part marked with `<sciebo key>` should be saved in `SCIEBO_KEY`.
- `SCIEBO_PASSWORD`: You should also create a password for the shared URL. The very same password get's stored in this variable.
- `TESTPYPI_TOKEN`: This is the API token to upload the project to TestPyPI.
- `PYPI_TOKEN`: This is the API token to upload the project to PyPI.

Make sure to define these variables as **protected** and **masked**. If you generate an sciebo link, it should have permissions to upload **and** change files. The ability to change files is needed to overwrite the executables with new versions.

[semver]: https://semver.org/ "Semantic Versioning"
[gitflow]: https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow "Gitflow Workflow"
[reference-style]: https://www.markdownguide.org/basic-syntax/#reference-style-links
