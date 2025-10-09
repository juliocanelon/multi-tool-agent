# Instrucción para coding agent
Repo: https://github.com/juliocanelon/java-app-test-agent
Branch: main
Checkmarx Project: 
Severidades objetivo: HIGH

## Hallazgos prioritarios (del CSV)
- [HIGH] Sql_Injection — src/main/java/com/example/vulnerableapp/VulnerableServlet.java:111 — SQL Injection due to string concatenation in query
- [HIGH] Reflected_XSS — src/main/java/com/example/vulnerableapp/VulnerableServlet.java:131 — Reflected XSS in 'name' parameter
- [HIGH] Stored_XSS — src/main/java/com/example/vulnerableapp/VulnerableServlet.java:163 — Stored XSS in 'comment' parameter insertion
- [HIGH] Path_Traversal — src/main/java/com/example/vulnerableapp/VulnerableServlet.java:177 — Path Traversal vulnerability in file access
- [HIGH] SSRF — src/main/java/com/example/vulnerableapp/VulnerableServlet.java:202 — Server-Side Request Forgery via 'url' parameter
- [HIGH] Log_Forging — src/main/java/com/example/vulnerableapp/VulnerableServlet.java:225 — Log Forging with unsanitized 'username' parameter
- [HIGH] Path_Traversal — src/main/java/com/example/vulnerableapp/SafeFileHandler.java:36 — Path Traversal due to user-controlled filename

## Tareas
1) Corregir hallazgos listados.
2) Generar breve changelog.