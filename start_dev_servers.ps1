# AI Recruitment Platform - Development Servers
Write-Host "AI Recruitment Platform - Development Server" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Yellow
Write-Host "FastAPI Server: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Streamlit Test App: http://localhost:8501" -ForegroundColor Cyan
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Yellow

# Start FastAPI server in background
Write-Host "Starting FastAPI server..." -ForegroundColor Blue
Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload" -WindowStyle Hidden

# Wait a moment for FastAPI to start
Start-Sleep -Seconds 3

# Start Streamlit app
Write-Host "Starting Streamlit test app..." -ForegroundColor Blue
python -m streamlit run streamlit_test_app.py --server.port 8501 --server.address 0.0.0.0
