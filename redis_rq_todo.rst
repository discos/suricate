Lanciare il worker::

    $ rqworker -P ~/suricate/suricate discos-api

.. note:: Questo è il path di sviluppo. In produzione?

Lanciare suricate-server::

    $ suricate-server start
   
Eseguire::

    $ curl -X POST http://localhost:5000/cmd/getTpi

Implementare il test usando un mocker.
