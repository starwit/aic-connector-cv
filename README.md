# AI Cockpit Connector for Computer Vision

This component sends sae detection results to ai-cockpit and adds images with bounding boxes to ai-cockpits minio bucket and creates a new decision for human operators to check.

## Background & Concept
AI software makes complex decisions and thus it is necessary to keep humans in control. In order to have a central place for this kind of checks [AI Cockpit](https://github.com/starwit/ai-cockpit) was developed. 

To get decisions into cockpit connecting components are necessary and this component connects object detection events to AI Cockpit. Decisions checked here are fairly simple - test if detections are correct. If you want to develop your own connector, this project can serve as a template. 

# Development
This section contains all info how to setup local development. 

## Check prerequisites
In order to work with this repository, you need to ensure the following steps:
- Install Poetry
- Install Docker

## Setup
- Run `poetry install`, this should install all necessary dependencies
- Start docker compose version of the SAE (see here: https://github.com/starwit/starwit-awareness-engine/blob/main/docker-compose/README.md)
- Run `poetry run python main.py`. If you see log messages like `Received SAE message from pipeline`, everything works as intended.

## Configuration
This template employs pydantic-settings for configuration handling. On startup, the following happens:
1. Load defaults (see `config.py`)
2. Read settings `settings.yaml` if it exists
3. Search through environment variables if any match configuration parameters (converted to upper_snake_case, nested levels delimited by `__`), overwriting the corresponding setting
4. Validate settings hierarchy if all necessary values are filled, otherwise Pydantic will throw a hopefully helpful error

The `settings.template.yaml` should always reflect a correct and fully fledged settings structure to use as a starting point for users. 

`redis_input.decision_type_names` optionally maps configured stream IDs to existing AI Cockpit decision type names. When configured, it must contain a non-empty decision type name for every subscribed `stream_id`; keys exclude the Redis stream prefix. Omitting the mapping preserves the existing AI Cockpit default decision type behavior.

## MinIO output

When HTTP output is configured, the connector stores three files in one MinIO directory before submitting the Cockpit decision:

- `original.jpg` is the unchanged frame used when creating a CVAT task.
- `annotated.jpg` contains the review overlay displayed in AI Cockpit.
- `detections.json` contains the detector labels and normalized bounding boxes that AI Cockpit imports as editable CVAT rectangles.

`detections.json` has the following format. Labels come from `SaeMessage.model_metadata.class_names`, and bounding-box coordinates are normalized to the original image size. No class list is configured in the connector.

```json
[
  {
    "label": "example-class",
    "boundingBox": {
      "minX": 0.1,
      "minY": 0.2,
      "maxX": 0.3,
      "maxY": 0.4
    }
  }
]
```

## Github Workflows and Versioning

The following Github Actions are available:

* [PR build](.github/workflows/pr-build.yml): Builds python project for each pull request to main branch. `poetry install` and `poetry run pytest` are executed, to compile and test python code.
* [Build and publish latest image](.github/workflows/build-publish-latest.yml): Manually executed action. Same like PR build. Additionally puts latest docker image to internal docker registry.
* [Create release](.github/workflows/create-release.yml): Manually executed action. Creates a github release with tag, docker image in internal docker registry, helm chart in chartmuseum by using and incrementing the version in pyproject.toml. Poetry is updating to next version by using "patch, minor and major" keywords. If you want to change to non-incremental version, set version in directly in pyproject.toml and execute create release afterwards.

## Dependabot Version Update

With [dependabot.yml](.github/dependabot.yml) a scheduled version update via Dependabot is configured. Dependabot creates a pull request if newer versions are available and the compilation is checked via PR build.
