# 1. uv 설치 이미지를 가져옴
FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 의존성 파일 복사 (캐싱 활용)
COPY pyproject.toml uv.lock ./

# 4. uv.lock 기반으로 라이브러리 설치
# --frozen: uv.lock을 업데이트하지 않고 고정된 상태로 설치
# --no-install-project: 소스 코드 복사 전 의존성만 미리 설치 (캐싱 최적화)
RUN uv sync --frozen --no-install-project --no-dev

# 5. 소스 코드 복사
COPY . .

# 6. 실행 (uv가 관리하는 환경 내에서 실행)
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]