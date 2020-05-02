#!/bin/bash
#Password = AGH2OSystemMaster!
echo "Creating key 'betatest'"
sudo -u postgres psql -d agh2odb -c "INSERT INTO keys VALUES('betatest','4-20',0,0)"



