==================
 Replica Chat API
==================

Free partial implementation of https://chat-api.com

Known issues
------------

* accepting file from replica instance to odoo is not implemented
* sending file from odoo to replica instance is not implemented

Configuration
-------------

1. Create whatsapp account. It will be used as a bot

2. Run:

.. code-block:: sh

   docker-compose up -d firefox

3. Using VNC client connect to 127.0.0.1:5900. Password is ``secret``
   Note, if you are running this on remote machine, consider to make SSH tunnel to that machine

4. In VNC client run:

   firefox -P

5. Press ``Create Profile`` -> ``Next`` -> Enter any profile name -> Press ``Finish``

6. Choose new created profile and press ``Start Firefox``

7. In address bar enter ``https://web.whatsapp.com``

8. Scan QR code

9. In address bar enter ``http://127.0.0.1:5000/admin``

10. Choose profile, that you have created some steps ago

11. Press "Generate access token"

12. Use this access token to access it's api
