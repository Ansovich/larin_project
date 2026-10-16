# DevOps Test API Project

## 1. Описание проекта
Проект представляет собой API на Python (FastAPI), развернутое в Kubernetes с использованием Helm.

**Основные компоненты:**
- **Приложение**: FastAPI с эндпоинтами /req, /history, /healthz, /readyz, /metrics
- **База данных**: PostgreSQL (StatefulSet, доступ только изнутри кластера)
- **CI/CD**: GitLab CI (тесты, линтинг, сборка, Trivy security scan, деплой)
- **Мониторинг**: PrometheusRule для алертинга на 5xx ошибки > 5%

## 2. Инструкция для локального запуска приложения
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --host 0.0.0.0 --port 8000

## 3. Инструкция для локальной сборки docker-образа
    docker build --provenance=false --sbom=false -t devops-api:local .

## 4. Инструкция для локального запуска контейнера
    docker run -d --name devops-api -p 8000:8000 --read-only --tmpfs /tmp -e DATABASE_URL=postgresql://user:pass@host:5432/db devops-api:local

## 5. Инструкция по развертыванию в kubernetes
    helm upgrade --install devops-api ./helm-chart --set image.tag=COMMIT_SHA --namespace default

## 6. Описание CI/CD пайплайна
1. **test_job**: Установка зависимостей и запуск unit-тестов (pytest)
2. **lint_job**: Валидация Helm-манифестов (helm lint)
3. **build_job**: Сборка multi-stage Docker-образа, тегирование SHA-хешем, push в Registry (порт 5050)
4. **security_job**: Сканирование образа на CRITICAL уязвимости (Trivy)
5. **deploy_job**: Развертывание через Helm с использованием собранного тега

## 7. Инструкция по запуску нагрузочного теста
    k6 run load-test/script.js

**Ожидаемый результат:**
- RPS: ~10 req/s
- p(95) задержка: < 500ms
- Доля ошибок: < 5%
