import sys
sys.path.append('.')

from core.mvcm import Mvcm
from core.api_service import ApiService
from ui.main_app import MainApp

def main():
    mvcm_instance = Mvcm()
    controller = ApiService(mvcm_instance)

    app = MainApp(controller)
    app.mainloop()
if __name__ == "__main__":
    main()
