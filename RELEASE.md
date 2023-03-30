Before you start, make yourself familiar with [Semantic Versioning][semver].

## Release Workflow

The release workflow is mainly handled by GitHub Actions. There, especially the workflow defined in `.github/workflows/release.yml`.
A new release can be created by going to the actions tab and running the "Create New Release" action manually.
You can select the respective Semver increment (_PATCH_, _MINOR_, _MAJOR_) but it is recommended to leave this field empty.
In this case the respective increment will be determined by looking at successfully merged pull requests and which labels were associated to them.
The labels are also building the release notes for the new release.
The mapping is defined in `.github/changelog-config.json`.
After the release pipeline finished running there will be a new pull request opened by GitHub Actions in order to merge the new changelog entry into the main branch.
Delete the respective release branch after the merge.
Releases are tagged on their own release branches named `release/v<version-number>`.
Whenever there needs to be a hotfix for one of the versions, checkout the respective tag `v<version-number>`, recreate the release branch and start working on the hotfix.
Patched versions can then be released by running the "Create New Release" workflow on the respective release branch.

## Notes

The CI/CD pipeline needs API keys to be able to upload the compiled package to PyPI/TestPyPI. These API keys can be changed/added under *Settings -> CI/CD -> Variables*. Currently we have the following variables defined:

<!--
- `SCIEBO_KEY`: If you share a folder in sciebo you get a URL similar to `<sciebo server url>/index.php/s/<sciebo key>`. The part marked with `<sciebo key>` should be saved in `SCIEBO_KEY`.
- `SCIEBO_PASSWORD`: You should also create a password for the shared URL. The very same password get's stored in this variable.
-->
- `TESTPYPI_TOKEN`: This is the API token to upload the project to TestPyPI.
- `PYPI_TOKEN`: This is the API token to upload the project to PyPI.

Make sure to define these variables as **protected** and **masked**. If you generate a sciebo link, it should have permissions to upload **and** change files. The ability to change files is needed to overwrite the executables with new versions.

[semver]: https://semver.org/ "Semantic Versioning"