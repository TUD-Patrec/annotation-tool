Before you start, make yourself familiar with the [Semantic Versioning][semver] and also have a look at [Gitflow Workflow][gitflow]. Especially the section about **Release branches**.

## Release Workflow

If you plan on releasing a new version follow these steps:

1. Merge the `dev` branch into `master`.
2. Afterwards run `cz bump` (or `make bump`) **on the `master` branch** to bump the version number, update the changelog and create a version tag automatically. Then push everything by running
   ```
   git push
   git push --tags
   ```
   The GitLab CI/CD should take care of compiling and uploading the package to PyPI/TestPyPI.
3. Also merge back `master` into `dev` to reflect the version update onto the development branch.
4. Create a new release on the _Deployments -> Releases_ page in GitLab to trigger any notifications for subscribed users.

### Alpha and beta versions

Alpha and beta versions life on `dev`. If you want to publish a pre-release, follow step 2 above (**on the `dev` branch**) and add `--prerelease [alpha,beta]` to the `cz` command (or run `make bump-alpha`/`make bump-beta`).

## Notes

The CI/CD pipeline needs API keys to be able to upload the compiled package to PyPI/TestPyPI. These API keys can be changed/added under *Settings -> CI/CD -> Variables*. Currently we have the following variables defined:

<!--
- `SCIEBO_KEY`: If you share a folder in sciebo you get a URL similar to `<sciebo server url>/index.php/s/<sciebo key>`. The part marked with `<sciebo key>` should be saved in `SCIEBO_KEY`.
- `SCIEBO_PASSWORD`: You should also create a password for the shared URL. The very same password get's stored in this variable.
-->
- `TESTPYPI_TOKEN`: This is the API token to upload the project to TestPyPI.
- `PYPI_TOKEN`: This is the API token to upload the project to PyPI.

Make sure to define these variables as **protected** and **masked**. If you generate an sciebo link, it should have permissions to upload **and** change files. The ability to change files is needed to overwrite the executables with new versions.

[semver]: https://semver.org/ "Semantic Versioning"
[gitflow]: https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow "Gitflow Workflow"
[reference-style]: https://www.markdownguide.org/basic-syntax/#reference-style-links
