# Contributing guide
Welcome! We are happy you are reading this, as we need developers to improve the project further.

## Ways to contribute
There are many ways to contribute to the project, including:
- New features
- Bug fixes
- Documentation
- Suggestions
- Tests

## How to contribute
Before opening an issue, please read other active issues.
Be sure to include an appropriate title and description.
All relevant information should be clearly stated.
If you wrote a patch, open a new pull request.

## Development environment
To start the development environment, run the `start` command with appropriate flags:
```
./server.sh start -dp
```
It will start the development environment and push the images to a local registry. Windows is currently not supported.

## Code style
For Python applications, use `isort` and `black` formatters. For Scala applications, use `scalafmt`.
