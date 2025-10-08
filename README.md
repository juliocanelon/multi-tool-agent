## MVP — cómo correr

1) Instala deps:
```bash
pip install -r requirements-mvp.txt
```

Copia .env.example a .env y completa GITHUB_TOKEN.

(Opcional) Autenticación GCP en el host:
```bash
gcloud auth application-default login
```

Coloca tu data/checkmarx.csv.

Ejecuta:
```bash
python run_mvp.py --config config/mvp.yaml
```

Por defecto commanding.mode = STUB (devuelve un diff mínimo).
Para usar Docker + Gemini CLI, construye tu imagen y cambia commanding.mode a DOCKER_GEMINI.

---

## ¿Por dónde empezamos hoy?
Empieza pegando **Prompt 1 → 2 → 3**. Luego corre `python run_mvp.py` en modo **STUB** para ver que:
- clona el repo,
- crea la rama `fix/ai-xxxxx`,
- aplica un diff chiquito,
- hace commit y push,
- abre PR.

Cuando eso funcione, pasamos a **Prompt 5 (DOCKER_GEMINI)** para reemplazar el STUB por tu CLI real.
