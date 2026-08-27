#!/bin/bash
cd ~/corp-bot-webapp
echo " Комментарий:"
read MSG
git add -A
git commit -m "$MSG"
git push origin main
echo "✅ Готово! Render обновится."
