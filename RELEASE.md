Before you start, make yourself familiar with the [Semantic Versioning][semver] and also have a look at [Gitflow Workflow][gitflow]. Especially the section about **Release branches**.

## Release Workflow

If you plan on releasing a new version follow these steps:

1. Create a new branch off of `dev` called `release/<version_of_the_release>`.
2. On the new release branch you perform all release related tasks, such as bumping the version number in the `pyproject.toml` (Note: The offical version number in `pyproject.toml` should not start with a 'v' as in the tags). No new features should be implemented on this branch, "only bug fixes, documentation generation, and other release-oriented tasks should go in this branch" (see the mentioned [page about Gitflow Workflow][2]). Also have a look at the [Release Checklist](#release-checklist).
3. Once ready, merge the release branch into `main` and tag the merge commit with the version number. Make sure that you actually create a merge commit by specifiying `--no-ff` if you use git on the command line.
4. Also merge the branch back into `dev`.
5. Now you can delete the release branch. The GitLab CI/CD should take care of compiling and uploading the package to PyPI/TestPyPI.

## Release Checklist

The following ToDos need to be completed on a release branch. (see above)

- [ ] Bump the version number in `pyproject.toml`. It should adhere to [semver][semver]. Do not prepend the version with 'v'. This should only be done for the git tags.
- [ ] Update `Changelog.md`. Make sure to leave a blank line between bullet points and headers.
    - [ ] Move changes from section `[Unreleased]` to it's own version section (see template below).
    - [ ] Add link to diff to the previous version as a [reference style link][reference-style] at the bottom of the page (`[<new version>]: <gitlab_url>/-/compare/<previous version>...<new version>`).
    - [ ] Update the reference style link of `unreleased` to `<gitlab_url>/-/compare/<new version>...dev`.


## Changelog Version Template

```markdown
## [Unreleased]

### Added

- 

### Changed

- 

### Deprecated

- 

### Removed

- 

### Fixed

- 

### Security

- 

## [<new version>] - yyyy-mm-dd
```

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
