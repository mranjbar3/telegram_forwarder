#!/bin/sh
# اجرای روزانه بکاپ داخل کانتینر اختصاصی
while true; do
  echo "[backup] starting..."
  python -c "from app.workers.tasks import run_backup; print(run_backup())"
  echo "[backup] sleeping 24h..."
  sleep 86400
done
