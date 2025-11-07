# Как запустить проект


## 1) Проверить установку Python
```bash
# windows
python --version
# macos/linux
python3 --version 
```
1. Если команда не найдена — установите Python с [python.org](https://www.python.org).
2. Не забудьте поставить галочку "Добавить в PATH"

## 2) Создать окружение

### Windows (CMD или PowerShell или консоль Pycharm)
```powershell
# в папке проекта
python -m venv .venv
```

### macOS / Linux (bash/zsh)
```bash
# в папке проекта
python3 -m venv .venv
```

## 3) Активировать окружение

### Windows
- **PowerShell**
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
  Если получаете ошибку про политику выполнения (Execution Policy):
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
  ```
- **CMD**
  ```cmd
  .\.venv\Scripts\activate.bat
  ```

### macOS / Linux (bash/zsh)
```bash
source .venv/bin/activate
```

## 4) Обновить `pip` и устанавливать пакеты
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 5) Запустить проект 

```bash
# если вы не в папке src/ 
cd src
# запускаем
python run.py
```

## 6) Заходим на сайт

Перейдите по ссылке http://localhost:5001