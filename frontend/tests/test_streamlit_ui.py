import os,sys,threading,tempfile
from pathlib import Path
TMP=Path(__file__).resolve().parents[1]/'.tmp';TMP.mkdir(exist_ok=True);tempfile.tempdir=str(TMP)
from werkzeug.serving import make_server
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'backend'))
from app import app
from streamlit.testing.v1 import AppTest

server=None;thread=None
def setup_module():
 global server,thread
 server=make_server('127.0.0.1',0,app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();os.environ['PAYAHEAD_API_URL']=f'http://127.0.0.1:{server.server_port}/api'
def teardown_module():
 if server:server.shutdown()
def run_ui(page=None):
 path=Path(__file__).resolve().parents[1]/'streamlit_app.py'; test=AppTest.from_file(str(path),default_timeout=30)
 if page:test.session_state['page_selector']=page
 return test.run()
def test_dashboard_renders_with_api():
 result=run_ui();assert not result.exception;assert any('Your money, in focus.' in t.value for t in result.title)
def test_preferences_page_renders_in_guest_mode():
 result=run_ui('Preferences');assert not result.exception;assert any('Your saved preferences' in t.value for t in result.subheader)
