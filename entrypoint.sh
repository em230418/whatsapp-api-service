#!/usr/bin/env sh
cd /opt/app
export FLASK_APP=whatsapp_api_service
if [ ! -f $FIREFOX_PROFILE_DIR/whatsapp_api_service.sqlite3 ]; then
    sqlite3 $FIREFOX_PROFILE_DIR/whatsapp_api_service.sqlite3 < schema.sql
fi

# for development perposes, whatsapp-api package is also updated
if [ -d "/mnt/whatsapp-api" ]; then
    python3 -m pip install /mnt/whatsapp-api --upgrade
fi

flask run --host 0.0.0.0 &
/opt/bin/entry_point.sh
