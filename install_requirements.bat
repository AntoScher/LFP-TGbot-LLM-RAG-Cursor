@echo off
echo Установка зависимостей...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install python-telegram-bot==20.3 flask==2.2.5 flask-sqlalchemy==2.5.1
pip install langchain==0.0.284 chromadb==0.3.23
pip install sentence-transformers==2.2.2 python-dotenv==1.0.0
pip install unstructured==0.10.30 pypdf==3.17.0 python-docx==1.1.0
pip install tqdm==4.65.0 python-dateutil==2.8.2
echo Установка завершена!
pause