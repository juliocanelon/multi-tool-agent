# ADK Prompt Execution Check

To verify that the orchestrator-based agent can be invoked with a Checkmarx-style prompt, run:

```bash
python run_mvp.py "Escanea y corrige HIGH en https://github.com/juliocanelon/java-app-test-agent branch main"
```

This command loads the orchestrator, clones the repository, and proceeds through the scan/fix/verify stages. In environments without Docker installed, the command still succeeds but reports `DOCKER_NOT_FOUND` in the `fix` section, indicating that running the fixing container is optional.
