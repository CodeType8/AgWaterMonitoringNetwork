#test_basic.py

import os
import unittest

from api.models import db
from api import create_app

app = create_app()

#TEST_DB = 'test.db'

class BasicTests(unittest.TestCase):

	############################
    #### setup and teardown ####
    ############################
 
    # executed prior to each test
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://agh2o:test123@localhost:5432/agh2odb"
            #os.path.join(app.config['BASEDIR'], TEST_DB)
        self.app = app.test_client()
        
        with app.app_context():
        	db.drop_all()
        	db.create_all()
        	db.session.commit()
 
        self.assertEqual(app.debug, False)
 
    # executed after each test
    def tearDown(self):
        pass


###############
#### tests ####
###############
 
    def test_main_page(self):
        response = self.app.get('/indextest', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
 
 
if __name__ == "__main__":
    unittest.main()
