from views.root_app import RootApp
from services.mvcm import Mvcm
from services.excel_service import ExcelService
from controllers.server_controller import ServerController
from controllers.config_controller import ConfigController

def main():
    mvcm = Mvcm()
    excel = ExcelService()
    
    # Controllers get the services they need
    srv_ctrl = ServerController(mvcm)
    cfg_ctrl = ConfigController(mvcm)
    
    app = RootApp(mvcm, srv_ctrl, cfg_ctrl, excel)
    app.mainloop()

if __name__ == "__main__":
    main()
