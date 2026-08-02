FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /workspace

COPY pyproject.toml README.md LICENSE ./
COPY app api config context features media models orchestration ocr orchestrate personalization pipeline priority reasoning repositories retrieval router speech utils validation ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

COPY configs ./configs
COPY dataset ./dataset
COPY output ./output

ENTRYPOINT ["orchestrate"]
CMD ["health"]
