@echo off
cd /d D:\projects\twoven-ecommerce\admin
call D:\projects\twoven-ecommerce\admin\env\Scripts\activate.bat

echo [%DATE% %TIME%] -- Running migrations… 
python manage.py migrate --noinput

echo [%DATE% %TIME%] -- Collecting static files…
python manage.py collectstatic --noinput

echo [%DATE% %TIME%] -- Starting Waitress…
waitress-serve --listen=*:8000 admin.wsgi:application
