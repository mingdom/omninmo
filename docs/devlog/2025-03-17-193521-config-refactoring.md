# Config Refactoring Plan - 2025-03-17

## Summary
Created a plan to refactor the monolithic `config.yaml` file into multiple smaller, more focused YAML files organized by functionality. The goal is to improve maintainability and make it easier to work with different aspects of the configuration. Additionally, analyzed which configuration values are actively used vs. deprecated to reduce unused settings.

## Key Points
- Created a detailed plan in `docs/devplan/2025-03-17-config-refactoring-plan.md`
- Analyzed codebase to identify which config values are actually being used
- Discovered several deprecated sections from a previous Streamlit UI implementation
- Proposed splitting into 7 logical configuration files with clear status indicators:
  - model.yaml (actively used)
  - features.yaml (actively used)
  - app.yaml (partially used)
  - data.yaml (partially used)
  - rating.yaml (deprecated)
  - logging.yaml (deprecated)
  - charts.yaml (deprecated)
- Provided implementation details for the configuration loader
- Added clear comments to mark deprecated sections

## Next Steps
- Review the plan with the team
- Implement the configuration structure as outlined
- Update code to use the new configuration loading mechanism
- Test thoroughly to ensure everything works as expected 