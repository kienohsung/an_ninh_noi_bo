# Hướng dẫn chạy dự án với tính năng mới
1. chạy terminal số 1: 
    - cd id_card_extractor_service
    - python -m venv .venv
    - .\.venv\Scripts\activate
    - python.exe -m pip install --upgrade pip
    - pip install --upgrade google-generativeai
    - pip install -r requirements.txt
    - uvicorn main:app --host 0.0.0.0 --port 5009 --reload

2. Chạy terminal số 2 (backend):
    ```
    cd backend
    python -m venv .venv
    .\.venv\Scripts\activate
    python.exe -m pip install --upgrade pip
    pip install -r requirements.txt
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```

3. Chạy terminal số 3 (frontend):
    cd frontend
    npm install
    npm run dev